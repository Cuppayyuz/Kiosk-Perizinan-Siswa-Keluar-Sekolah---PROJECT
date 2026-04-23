import flet as ft
import requests
import json  
from datetime import datetime, timedelta

# =======================================================
# MASUKKAN LINK NGROK KAMU DI SINI
URL_BASE = "https://unconverged-paragraphistical-gemma.ngrok-free.dev"
# =======================================================

async def main(page: ft.Page):
    # 1. SETUP LAYAR UTAMA
    page.title = "Smart Exit"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    page.window.width = 360
    page.window.height = 640
    page.theme_mode = ft.ThemeMode.LIGHT

    prefs = ft.SharedPreferences()

    app_state = {
        "id_guru": None,
        "nama": "",
        "role": ""
    }

    # ==================================================
    # FUNGSI BANTUAN API & ALERT
    # ==================================================
    def show_snack(message, color=ft.Colors.RED):
        page.snack_bar = ft.SnackBar(ft.Text(message, color=ft.Colors.WHITE), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def fetch_api(endpoint, method="GET", json_data=None):
        url = f"{URL_BASE}{endpoint}"
        headers = {'ngrok-skip-browser-warning': 'true'}
        try:
            if method == "POST":
                res = requests.post(url, headers=headers, json=json_data, timeout=10, verify=False)
            else:
                res = requests.get(url, headers=headers, timeout=10, verify=False)
            return res.json(), None
        except Exception as e:
            return None, str(e)

    # ==================================================
    # LAYAR LOGIN
    # ==================================================
    def login_view():
        username_tb = ft.TextField(label="Username", prefix_icon=ft.Icons.ACCOUNT_CIRCLE, border_radius=8)
        password_tb = ft.TextField(label="Password", password=True, can_reveal_password=True, prefix_icon=ft.Icons.LOCK, border_radius=8)
        error_lbl = ft.Text(color=ft.Colors.ERROR, text_align=ft.TextAlign.CENTER)

        async def handle_login(e):
            if not username_tb.value or not password_tb.value:
                error_lbl.value = "Username dan Password wajib diisi!"
                page.update()
                return

            error_lbl.value = "Mencoba login..."
            error_lbl.color = ft.Colors.BLUE
            page.update()

            data, err = fetch_api("/api/mobile/login", "POST", {"username": username_tb.value, "password": password_tb.value})

            if err:
                error_lbl.value = f"Error: {err[:30]}..."
                error_lbl.color = ft.Colors.ERROR
                page.update()
                return

            if data and data.get('status') == 'sukses':
                if data['role'] == 'admin':
                    error_lbl.value = "Akses Ditolak! Admin wajib via Web."
                    error_lbl.color = ft.Colors.ERROR
                    page.update()
                    return

                app_state["id_guru"] = data['id_guru']
                app_state["nama"] = data['nama']
                app_state["role"] = data['role']

                user_dict = {
                    "id_guru": data['id_guru'],
                    "nama": data['nama'],
                    "role": data['role'],
                    "login_at": datetime.now().strftime('%Y-%m-%d')
                }
                await prefs.set("user_data", json.dumps(user_dict))

                username_tb.value = ""
                password_tb.value = ""
                error_lbl.value = ""
                
                await page.push_route("/dashboard")
            else:
                error_lbl.value = data.get('pesan', 'Gagal login') if data else "Gagal koneksi ke server."
                error_lbl.color = ft.Colors.ERROR
                page.update()

        # [PERBAIKAN FLET 1.0] Tambahkan route= secara eksplisit
        return ft.View(
            route="/login",
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("SMART EXIT", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE, text_align=ft.TextAlign.CENTER),
                            ft.Text("Login Portal", size=16, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=30),
                            username_tb,
                            password_tb,
                            error_lbl,
                            ft.Container(height=10),
                            ft.Button(
                                "MASUK", 
                                on_click=handle_login, 
                                width=400, 
                                height=50, 
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    bgcolor=ft.Colors.BLUE,
                                    color=ft.Colors.WHITE
                                )
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=25,
                    alignment=ft.Alignment.CENTER,
                    expand=True
                )
            ]
        )

    # ==================================================
    # LAYAR DASHBOARD GURU
    # ==================================================
    def dashboard_view():
        list_view = ft.ListView(expand=True, spacing=10)

        def load_history():
            list_view.controls.clear()
            list_view.controls.append(ft.ProgressBar())
            page.update()

            data, err = fetch_api(f"/api/mobile/riwayat_terbaru/{app_state['id_guru']}")
            list_view.controls.clear()

            if err:
                list_view.controls.append(ft.ListTile(title=ft.Text("GAGAL KONEK"), subtitle=ft.Text(err[:40], color=ft.Colors.RED)))
            elif not data:
                list_view.controls.append(ft.ListTile(title=ft.Text("Belum ada token"), subtitle=ft.Text("Belum ada riwayat tercatat.")))
            else:
                for baris in data:
                    ikon = ft.Icons.CHECK_CIRCLE if baris['status'] == "KELUAR" else ft.Icons.HOURGLASS_TOP
                    ikon_color = ft.Colors.GREEN if baris['status'] == "KELUAR" else ft.Colors.ORANGE
                    list_view.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ikon, color=ikon_color, size=35),
                            title=ft.Text(f"{baris['kode_token']} ({baris['jenis_izin']})", weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"Status: {baris['status']}\nDibuat: {baris['waktu_dibuat']}"),
                            is_three_line=True
                        )
                    )
            page.update()

        def action_logout(e):
            async def confirm_logout(e):
                dlg_logout.open = False
                await prefs.remove("user_data")
                app_state.update({"id_guru": None, "nama": "", "role": ""})
                await page.push_route("/login")

            dlg_logout = ft.AlertDialog(
                title=ft.Text("Keluar Aplikasi?"),
                content=ft.Text("Apakah Anda yakin ingin logout dari akun ini?"),
                actions=[
                    ft.TextButton("BATAL", on_click=lambda e: setattr(dlg_logout, 'open', False) or page.update()),
                    ft.TextButton("YA, KELUAR", on_click=confirm_logout, style=ft.ButtonStyle(color=ft.Colors.RED)),
                ],
            )
            page.overlay.append(dlg_logout)
            dlg_logout.open = True
            page.update()

        def action_izin(jenis):
            def submit_izin(e):
                dlg_izin.open = False
                page.update()

                data, err = fetch_api("/api/mobile/buat_token", "POST", {"jenis": jenis, "id_guru": app_state["id_guru"]})

                if err:
                    show_snack(f"Error Koneksi: {err[:50]}")
                elif data and data.get('status') == 'sukses':
                    dlg_info = ft.AlertDialog(
                        title=ft.Text("Berhasil!", color=ft.Colors.GREEN),
                        content=ft.Text(f"Kode Token {jenis}:\n\n{data['token']}\n\nBerikan kode ini ke siswa.", weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        actions=[ft.TextButton("TUTUP", on_click=lambda e: setattr(dlg_info, 'open', False) or page.update())]
                    )
                    page.overlay.append(dlg_info)
                    dlg_info.open = True
                    load_history()
                else:
                    show_snack("Gagal: Database menolak penyimpanan data.")

            dlg_izin = ft.AlertDialog(
                title=ft.Text(f"Izin {jenis}"),
                content=ft.Text(f"Terbitkan token {jenis} sekarang?"),
                actions=[
                    ft.TextButton("BATAL", on_click=lambda e: setattr(dlg_izin, 'open', False) or page.update()),
                    ft.TextButton("TERBITKAN", on_click=submit_izin),
                ],
            )
            page.overlay.append(dlg_izin)
            dlg_izin.open = True
            page.update()

        async def buka_semua_riwayat(e):
            await page.push_route("/riwayat")

        role_title = f"Pemantau: {app_state['nama']}" if app_state['role'] == 'pantau' else f"Guru: {app_state['nama']}"

        menu_buttons = ft.Row(
            controls=[
                ft.FilledButton("SAKIT", icon=ft.Icons.MEDICAL_SERVICES, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700), on_click=lambda e: action_izin("SAKIT")),
                ft.FilledButton("IZIN", icon=ft.Icons.MESSAGE, style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_600, color=ft.Colors.BLACK), on_click=lambda e: action_izin("IZIN")),
                ft.FilledButton("DISPEN", icon=ft.Icons.GROUPS, style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_700), on_click=lambda e: action_izin("DISPEN")),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            visible=(app_state['role'] != 'pantau')
        )

        load_history()

        # [PERBAIKAN FLET 1.0] Tambahkan route= secara eksplisit
        return ft.View(
            route="/dashboard",
            controls=[
                ft.AppBar(
                    title=ft.Text(role_title, size=18, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    actions=[
                        ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: load_history()),
                        ft.IconButton(ft.Icons.LOGOUT, on_click=action_logout, tooltip="Logout"),
                    ]
                ),
                ft.Container(content=menu_buttons, padding=10),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("5 Token Terakhir", weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
                            ft.TextButton("Lihat Semua ➔", on_click=buka_semua_riwayat) 
                        ], 
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=ft.padding.symmetric(horizontal=15, vertical=5)
                ),
                ft.Container(content=list_view, expand=True, padding=10)
            ]
        )

    # ==================================================
    # LAYAR SEMUA RIWAYAT
    # ==================================================
    def riwayat_view():
        list_view = ft.ListView(expand=True, spacing=10)

        def load_semua_riwayat():
            list_view.controls.clear()
            list_view.controls.append(ft.ProgressBar())
            page.update()

            data, err = fetch_api(f"/api/mobile/riwayat_semua/{app_state['id_guru']}")
            list_view.controls.clear()

            if err:
                list_view.controls.append(ft.ListTile(title=ft.Text("GAGAL KONEK"), subtitle=ft.Text(err[:40], color=ft.Colors.RED)))
            elif not data:
                list_view.controls.append(ft.ListTile(title=ft.Text("Kosong"), subtitle=ft.Text("Anda belum pernah membuat token.")))
            else:
                for baris in data:
                    ikon = ft.Icons.CHECK_CIRCLE if baris['status'] == "KELUAR" else ft.Icons.HOURGLASS_TOP
                    ikon_color = ft.Colors.GREEN if baris['status'] == "KELUAR" else ft.Colors.ORANGE
                    list_view.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ikon, color=ikon_color, size=35),
                            title=ft.Text(f"{baris['kode_token']} ({baris['jenis_izin']})", weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"Status: {baris['status']}\nDibuat: {baris['waktu_dibuat']}"),
                            is_three_line=True
                        )
                    )
            page.update()

        load_semua_riwayat()

        async def kembali_ke_dashboard(e):
            await page.push_route("/dashboard")

        # [PERBAIKAN FLET 1.0] Tambahkan route= secara eksplisit
        return ft.View(
            route="/riwayat",
            controls=[
                ft.AppBar(
                    leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=kembali_ke_dashboard),
                    title=ft.Text("Semua Riwayat Izin", size=18, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    actions=[ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: load_semua_riwayat())]
                ),
                ft.Container(content=list_view, expand=True, padding=10)
            ]
        )

    # ==================================================
    # SISTEM ROUTING FLET 1.0 (ASYNC BASED)
    # ==================================================
    def route_change(e=None):
        page.views.clear()
        if page.route == "/login":
            page.views.append(login_view())
        elif page.route == "/dashboard":
            page.views.append(dashboard_view())
        elif page.route == "/riwayat":
            page.views.append(riwayat_view())
        page.update()

    async def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        await page.push_route(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # ==================================================
    # AUTO LOGIN (PERSISTENT STORAGE)
    # ==================================================
    user_data_str = await prefs.get("user_data")
    
    if user_data_str:
        user_data = json.loads(user_data_str)
        tgl_login = datetime.strptime(user_data['login_at'], '%Y-%m-%d')
        
        if datetime.now() > tgl_login + timedelta(days=7):
            await prefs.remove("user_data")
            await page.push_route("/login") 
        else:
            app_state["id_guru"] = user_data['id_guru']
            app_state["nama"] = user_data['nama']
            app_state["role"] = user_data['role']
            await page.push_route("/dashboard") 
    else:
        await page.push_route("/login") 

if __name__ == "__main__":
    ft.run(main)