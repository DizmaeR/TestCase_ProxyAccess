import json
import sys

import requests
import websocket
from PyQt6.QtCore import QObject, QRunnable, Qt, QThread, QThreadPool, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

BASE_URL = "http://localhost:8002/api/v1"
WS_BASE = "ws://localhost:8002/ws/status"

STATUS_CONFIG: dict[str, tuple[str, str]] = {
    "connected": ("Подключено", "#2e7d32"),
    "disconnected": ("Отключено", "#757575"),
    "no_free_vms": ("Нет свободных прокси", "#c62828"),
    "error": ("Ошибка", "#c62828"),
}

PAGE_LOGIN = 0
PAGE_PROXY = 1


# ---------------------------------------------------------------------------
# WebSocket thread
# ---------------------------------------------------------------------------


class WSThread(QThread):
    status_received = pyqtSignal(str)

    def __init__(self, user_id: int) -> None:
        super().__init__()
        self.user_id = user_id
        self._ws: websocket.WebSocketApp | None = None

    def run(self) -> None:
        url = f"{WS_BASE}/{self.user_id}"

        def on_message(ws: websocket.WebSocketApp, message: str) -> None:
            try:
                data = json.loads(message)
                self.status_received.emit(data.get("status", ""))
            except Exception:
                self.status_received.emit(str(message))

        def on_error(ws: websocket.WebSocketApp, error: Exception) -> None:
            self.status_received.emit("error")

        self._ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error)
        self._ws.run_forever()

    def stop(self) -> None:
        if self._ws:
            self._ws.close()
        self.quit()
        self.wait()


# ---------------------------------------------------------------------------
# HTTP workers
# ---------------------------------------------------------------------------


class HttpSignals(QObject):
    success = pyqtSignal(dict)
    error = pyqtSignal(str)
    finished = pyqtSignal()


class LoginWorker(QRunnable):
    def __init__(self, email: str, password: str) -> None:
        super().__init__()
        self.email = email
        self.password = password
        self.signals = HttpSignals()

    def run(self) -> None:
        try:
            resp = requests.post(
                f"{BASE_URL}/auth/login",
                json={"email": self.email, "password": self.password},
                timeout=10,
            )
            resp.raise_for_status()
            self.signals.success.emit(resp.json())
        except requests.HTTPError as exc:
            try:
                detail = exc.response.json().get("detail", str(exc))
            except Exception:
                detail = str(exc)
            self.signals.error.emit(detail)
        except requests.ConnectionError:
            self.signals.error.emit("Не удалось подключиться к серверу.")
        except Exception as exc:
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()


class ProfileWorker(QRunnable):
    def __init__(self, token: str) -> None:
        super().__init__()
        self.token = token
        self.signals = HttpSignals()

    def run(self) -> None:
        try:
            resp = requests.get(
                f"{BASE_URL}/profile/",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10,
            )
            resp.raise_for_status()
            self.signals.success.emit(resp.json())
        except requests.HTTPError as exc:
            try:
                detail = exc.response.json().get("detail", str(exc))
            except Exception:
                detail = str(exc)
            self.signals.error.emit(detail)
        except requests.ConnectionError:
            self.signals.error.emit("Не удалось подключиться к серверу.")
        except Exception as exc:
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()


class ConnectWorker(QRunnable):
    def __init__(self, key: str) -> None:
        super().__init__()
        self.key = key
        self.signals = HttpSignals()

    def run(self) -> None:
        try:
            resp = requests.post(
                f"{BASE_URL}/proxy/activate-key",
                params={"key": self.key},
                timeout=10,
            )
            resp.raise_for_status()
            self.signals.success.emit(resp.json())
        except requests.HTTPError as exc:
            try:
                detail = exc.response.json().get("detail", str(exc))
            except Exception:
                detail = str(exc)
            self.signals.error.emit(detail)
        except requests.ConnectionError:
            self.signals.error.emit("Не удалось подключиться к серверу.")
        except Exception as exc:
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()


class DisconnectWorker(QRunnable):
    def __init__(self, token: str) -> None:
        super().__init__()
        self.token = token
        self.signals = HttpSignals()

    def run(self) -> None:
        try:
            resp = requests.post(
                f"{BASE_URL}/proxy/disconnect",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10,
            )
            resp.raise_for_status()
            self.signals.success.emit(resp.json())
        except requests.HTTPError as exc:
            try:
                detail = exc.response.json().get("detail", str(exc))
            except Exception:
                detail = str(exc)
            self.signals.error.emit(detail)
        except requests.ConnectionError:
            self.signals.error.emit("Не удалось подключиться к серверу.")
        except Exception as exc:
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Proxy Access")
        self.setFixedWidth(460)

        self._token: str | None = None
        self._user_id: int | None = None
        self._vm_id: int | None = None
        self._ws_thread: WSThread | None = None
        self._pool = QThreadPool()

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)
        self._stack.addWidget(self._build_login_page())  # PAGE_LOGIN = 0
        self._stack.addWidget(self._build_proxy_page())  # PAGE_PROXY = 1
        self._stack.setCurrentIndex(PAGE_LOGIN)

    # --- Login page ---

    def _build_login_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        layout.setContentsMargins(32, 32, 32, 32)

        title = QLabel("Proxy Access")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title)

        subtitle = QLabel("Войдите в аккаунт")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #888;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(8)
        layout.addWidget(self._separator())
        layout.addSpacing(4)

        layout.addWidget(self._hint("Email"))
        self.inp_email = QLineEdit()
        self.inp_email.setPlaceholderText("user@example.com")
        self.inp_email.setMinimumHeight(36)
        self.inp_email.returnPressed.connect(self._on_login)
        layout.addWidget(self.inp_email)

        layout.addSpacing(4)
        layout.addWidget(self._hint("Пароль"))
        self.inp_password = QLineEdit()
        self.inp_password.setPlaceholderText("••••••••")
        self.inp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_password.setMinimumHeight(36)
        self.inp_password.returnPressed.connect(self._on_login)
        layout.addWidget(self.inp_password)

        layout.addSpacing(4)

        self.lbl_login_error = QLabel()
        self.lbl_login_error.setStyleSheet("color: #c62828;")
        self.lbl_login_error.setWordWrap(True)
        self.lbl_login_error.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self.lbl_login_error)

        self.btn_login = QPushButton("Войти")
        self.btn_login.setMinimumHeight(44)
        self.btn_login.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_login.setStyleSheet(
            """
            QPushButton          { background:#1976d2; color:white;
            border:none; border-radius:7px; }
            QPushButton:hover    { background:#1565c0; }
            QPushButton:pressed  { background:#0d47a1; }
            QPushButton:disabled { background:#bbdefb; color:#78909c; }
            """
        )
        self.btn_login.clicked.connect(self._on_login)
        layout.addWidget(self.btn_login)

        layout.addStretch()
        return page

    # --- Proxy page ---

    def _build_proxy_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        layout.setContentsMargins(32, 28, 32, 28)

        # Header row: title + logout button
        header = QHBoxLayout()
        title = QLabel("Proxy Access")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()
        self.btn_logout = QPushButton("Выйти")
        self.btn_logout.setFont(QFont("Segoe UI", 9))
        self.btn_logout.setFixedHeight(28)
        self.btn_logout.setStyleSheet(
            """
            QPushButton          { background:transparent; color:#888;
            border:1px solid #ccc; border-radius:5px; padding:0 10px; }
            QPushButton:hover    { color:#333; border-color:#999; }
            QPushButton:pressed  { background:#f5f5f5; }
            """
        )
        self.btn_logout.clicked.connect(self._on_logout)
        header.addWidget(self.btn_logout)
        layout.addLayout(header)

        layout.addWidget(self._separator())

        # Status
        layout.addWidget(self._hint("Статус подключения"))
        self.lbl_status = QLabel()
        self.lbl_status.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        layout.addWidget(self.lbl_status)

        layout.addWidget(self._separator())

        # Key input
        layout.addWidget(self._hint("Ключ активации"))
        self.inp_key = QLineEdit()
        self.inp_key.setPlaceholderText("Вставьте ваш ключ активации")
        self.inp_key.setMinimumHeight(36)
        self.inp_key.returnPressed.connect(self._on_connect)
        layout.addWidget(self.inp_key)

        layout.addSpacing(2)

        # Proxy error
        self.lbl_proxy_error = QLabel()
        self.lbl_proxy_error.setStyleSheet("color: #c62828;")
        self.lbl_proxy_error.setWordWrap(True)
        self.lbl_proxy_error.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self.lbl_proxy_error)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_connect = QPushButton("Подключиться")
        self.btn_connect.setMinimumHeight(44)
        self.btn_connect.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_connect.setStyleSheet(
            """
            QPushButton          { background:#1976d2; color:white;
            border:none; border-radius:7px; }
            QPushButton:hover    { background:#1565c0; }
            QPushButton:pressed  { background:#0d47a1; }
            QPushButton:disabled { background:#bbdefb; color:#78909c; }
            """
        )
        self.btn_connect.clicked.connect(self._on_connect)
        btn_row.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Отключиться")
        self.btn_disconnect.setMinimumHeight(44)
        self.btn_disconnect.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.setStyleSheet(
            """
            QPushButton          { background:#d32f2f; color:white;
             border:none; border-radius:7px; }
            QPushButton:hover    { background:#c62828; }
            QPushButton:pressed  { background:#b71c1c; }
            QPushButton:disabled { background:#ffcdd2; color:#78909c; }
            """
        )
        self.btn_disconnect.clicked.connect(self._on_disconnect)
        btn_row.addWidget(self.btn_disconnect)

        layout.addLayout(btn_row)
        layout.addWidget(self._separator())

        # VM info
        layout.addWidget(self._hint("Данные прокси-сервера"))

        self.lbl_host = QLabel("—")
        self.lbl_port = QLabel("—")
        self.lbl_protocol = QLabel("—")

        for label_text, value_lbl in [
            ("Хост:", self.lbl_host),
            ("Порт:", self.lbl_port),
            ("Протокол:", self.lbl_protocol),
        ]:
            row = QHBoxLayout()
            key_lbl = QLabel(label_text)
            key_lbl.setFixedWidth(80)
            key_lbl.setFont(QFont("Segoe UI", 10))
            key_lbl.setStyleSheet("color: #555;")
            value_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            row.addWidget(key_lbl)
            row.addWidget(value_lbl)
            row.addStretch()
            layout.addLayout(row)

        layout.addStretch()
        return page

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _hint(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 8))
        lbl.setStyleSheet("color: #999;")
        return lbl

    def _separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #e0e0e0;")
        return line

    def _set_status(self, status: str) -> None:
        label, color = STATUS_CONFIG.get(status, ("Неизвестно", "#757575"))
        self.lbl_status.setText(label)
        self.lbl_status.setStyleSheet(f"color: {color};")
        connected = status == "connected"
        self.btn_connect.setEnabled(not connected)
        self.btn_disconnect.setEnabled(connected)

    def _set_vm_info(self, host: str, port: int, protocol: str) -> None:
        self.lbl_host.setText(host)
        self.lbl_port.setText(str(port))
        self.lbl_protocol.setText(protocol.upper())

    def _clear_vm_info(self) -> None:
        for lbl in (self.lbl_host, self.lbl_port, self.lbl_protocol):
            lbl.setText("—")

    # ------------------------------------------------------------------
    # Login flow
    # ------------------------------------------------------------------

    def _on_login(self) -> None:
        email = self.inp_email.text().strip()
        password = self.inp_password.text()
        if not email or not password:
            self.lbl_login_error.setText("Введите email и пароль.")
            return
        self.lbl_login_error.setText("")
        self.btn_login.setEnabled(False)
        self.btn_login.setText("Вход…")

        worker = LoginWorker(email, password)
        worker.signals.success.connect(self._on_login_ok)
        worker.signals.error.connect(self._on_login_err)
        worker.signals.finished.connect(self._on_login_done)
        self._pool.start(worker)

    def _on_login_ok(self, data: dict) -> None:
        self._token = data.get("access_token", "")
        # Fetch profile to get user_id, then open WS with correct channel
        worker = ProfileWorker(self._token)
        worker.signals.success.connect(self._on_profile_ok)
        worker.signals.error.connect(self._on_profile_err)
        self._pool.start(worker)

    def _on_profile_ok(self, data: dict) -> None:
        self._user_id = data["id"]
        self._start_ws(self._user_id)
        self._set_status("disconnected")
        self.lbl_proxy_error.setText("")
        self._stack.setCurrentIndex(PAGE_PROXY)

    def _on_profile_err(self, msg: str) -> None:
        # Still allow entering proxy page, WS just won't work
        self._set_status("disconnected")
        self.lbl_proxy_error.setText("")
        self._stack.setCurrentIndex(PAGE_PROXY)

    def _on_login_err(self, msg: str) -> None:
        self.lbl_login_error.setText(f"Ошибка: {msg}")

    def _on_login_done(self) -> None:
        self.btn_login.setEnabled(True)
        self.btn_login.setText("Войти")

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def _on_logout(self) -> None:
        self._stop_ws()
        self._token = None
        self._user_id = None
        self._vm_id = None
        self._clear_vm_info()
        self.inp_email.clear()
        self.inp_password.clear()
        self.lbl_login_error.setText("")
        self._stack.setCurrentIndex(PAGE_LOGIN)

    # ------------------------------------------------------------------
    # Connect flow
    # ------------------------------------------------------------------

    def _on_connect(self) -> None:
        key = self.inp_key.text().strip()
        if not key:
            self.lbl_proxy_error.setText("Введите ключ активации.")
            return
        self.lbl_proxy_error.setText("")
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("Подключение…")

        worker = ConnectWorker(key)
        worker.signals.success.connect(self._on_connect_ok)
        worker.signals.error.connect(self._on_connect_err)
        worker.signals.finished.connect(self._on_connect_done)
        self._pool.start(worker)

    def _on_connect_ok(self, data: dict) -> None:
        self._vm_id = data["id"]
        self._set_vm_info(data["host"], data["port"], data["protocol"])
        self._set_status("connected")
        self.inp_key.clear()
        if self._user_id:
            self._start_ws(self._user_id)

    def _on_connect_err(self, msg: str) -> None:
        self.lbl_proxy_error.setText(f"Ошибка: {msg}")
        self._set_status("error")

    def _on_connect_done(self) -> None:
        self.btn_connect.setText("Подключиться")
        if self.lbl_status.text() != STATUS_CONFIG["connected"][0]:
            self.btn_connect.setEnabled(True)

    # ------------------------------------------------------------------
    # Disconnect flow
    # ------------------------------------------------------------------

    def _on_disconnect(self) -> None:
        self.lbl_proxy_error.setText("")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.setText("Отключение…")

        worker = DisconnectWorker(self._token or "")
        worker.signals.success.connect(self._on_disconnect_ok)
        worker.signals.error.connect(self._on_disconnect_err)
        worker.signals.finished.connect(self._on_disconnect_done)
        self._pool.start(worker)

    def _on_disconnect_ok(self, _data: dict) -> None:
        self._stop_ws()
        self._set_status("disconnected")
        self._clear_vm_info()
        self._vm_id = None

    def _on_disconnect_err(self, msg: str) -> None:
        self.lbl_proxy_error.setText(f"Ошибка: {msg}")
        self.btn_disconnect.setEnabled(True)

    def _on_disconnect_done(self) -> None:
        self.btn_disconnect.setText("Отключиться")

    # ------------------------------------------------------------------
    # WebSocket
    # ------------------------------------------------------------------

    def _start_ws(self, user_id: int) -> None:
        self._stop_ws()
        self._ws_thread = WSThread(user_id)
        self._ws_thread.status_received.connect(self._set_status)
        self._ws_thread.start()

    def _stop_ws(self) -> None:
        if self._ws_thread and self._ws_thread.isRunning():
            self._ws_thread.stop()
        self._ws_thread = None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._stop_ws()
        self._pool.waitForDone(3000)
        super().closeEvent(event)


# ---------------------------------------------------------------------------


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
