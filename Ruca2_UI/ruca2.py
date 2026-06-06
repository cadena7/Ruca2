#!/usr/bin/python3

import datetime
import json

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GLib, Pango

import c_filtros_ruca2_mqtt


class MainApp():

    ENGINEERING_STATE_SECTIONS = (
        ("Estado general", (
            "RUEDA_ESTADO",
            "RUEDA_PARO_EMERGENCIA",
            "RUEDA_SPEED",
        )),
        ("Posiciones", (
            "RUEDA_INDICE",
            "RUEDA_INDICE_SET",
            "POLARIZA_INDICE",
            "POLARIZA_INDICE_SET",
            "REDUCTOR_INDICE",
            "REDUCTOR_SET",
        )),
        ("Inicialización", (
            "FIRST_INIT_RUEDA",
            "FIRST_INIT_POLARIZA",
            "FIRST_INIT_REDUCTOR",
        )),
        ("Frenos y sensores", (
            "RUEDA_FRENO",
            "RUEDA_FRENO_SENSOR",
            "POLARIZA_FRENO",
            "POLARIZA_FRENO_SENSOR",
            "REDUCTOR_FRENO",
        )),
        ("Contadores y entradas", (
            "RUEDA_PASOS",
            "POLARIZA_PASOS",
            "REDUCTOR_PASOS",
            "RUEDA_SWITCH",
            "RUEDA_INICIO",
            "POLARIZA_INICIO",
            "REDUCTOR_AZUL",
            "REDUCTOR_ROJO",
            "REDUCTOR_FUERA",
            "B_START",
            "B_STOP",
            "B_UP",
            "B_DOWN",
        )),
    )

    ENGINEERING_BLUE_VALUES = {
        "RUEDA_SPEED",
        "RUEDA_INDICE",
        "RUEDA_INDICE_SET",
        "POLARIZA_INDICE",
        "POLARIZA_INDICE_SET",
        "REDUCTOR_INDICE",
        "REDUCTOR_SET",
    }


    def __init__(self):

        print("Arrancando GUI")

        self.Ruca = c_filtros_ruca2_mqtt.RUCA(
            self.carga_datos_ui
        )

        builder = Gtk.Builder()
        builder.add_from_file("ruca2.glade")
        builder.connect_signals(self)

        self.engineering_access_authorized = False
        self.previous_notebook_page = 0
        self.restoring_notebook_page = False


        # ================= FILTROS =================
        self.c_filtros = builder.get_object("c_filtros")
        self.lfiltros = Gtk.ListStore(str)

        for d in self.Ruca.lista_filtros:
            self.lfiltros.append([d])

        self.c_filtros.set_model(self.lfiltros)

        cell = Gtk.CellRendererText()
        self.c_filtros.pack_start(cell, True)
        self.c_filtros.add_attribute(cell, 'text', 0)

        self.c_filtros.set_active(0)

        self.c_filtros.connect(
            "changed",
            self.on_filtros_combo_changed
        )


        # ================= REDUCTOR =================
        self.c_reductor = builder.get_object("c_reductor")

        self.lreductor = Gtk.ListStore(str, int)

        for d in self.Ruca.lista_reductor:
            self.lreductor.append([d[0], d[1]])

        self.c_reductor.set_model(self.lreductor)

        cell = Gtk.CellRendererText()
        self.c_reductor.pack_start(cell, True)
        self.c_reductor.add_attribute(cell, 'text', 0)

        self.c_reductor.set_active(0)

        self.c_reductor.connect(
            "changed",
            self.c_reductor_changed
        )


        # ================= ESTADOS =================
        self.e_filtro = builder.get_object("e_filtro")
        self.e_switch = builder.get_object("e_switch")
        self.e_estado = builder.get_object("e_estado")


        # ================= INGENIERÍA =================
        self.engineering_host = builder.get_object("engineering_host")
        self.engineering_port = builder.get_object("engineering_port")
        self.engineering_speed = builder.get_object("engineering_speed")
        self.engineering_current_speed = builder.get_object(
            "engineering_current_speed"
        )
        self.engineering_status = builder.get_object("engineering_status")
        self.engineering_controls = builder.get_object("engineering_controls")
        self.main_notebook = builder.get_object("main_notebook")
        self.help_page = builder.get_object("help_page")
        self.help_text_view = builder.get_object("help_text_view")
        self.engineering_page = builder.get_object("engineering_page")
        self.engineering_connection = builder.get_object(
            "engineering_connection"
        )
        self.engineering_last_update = builder.get_object(
            "engineering_last_update"
        )
        self.engineering_state_tree = builder.get_object(
            "engineering_state_tree"
        )
        self.engineering_move_motor = builder.get_object(
            "engineering_move_motor"
        )
        self.engineering_move_direction = builder.get_object(
            "engineering_move_direction"
        )
        self.engineering_move_steps = builder.get_object(
            "engineering_move_steps"
        )

        self.engineering_state_model = Gtk.ListStore(
            str,
            str,
            str,
            str,
            int
        )
        self.engineering_state_tree.set_model(self.engineering_state_model)
        self.add_engineering_state_column("Variable", 1)
        self.add_engineering_state_column("Valor", 2)
        self.populate_engineering_state({})
        self.set_direct_connection(False, "Sin consultar")
        self.configure_help_view()


        # ================= VENTANA =================
        self.window = builder.get_object("window1")
        self.window.connect("destroy", self.salida)
        self.window.show_all()

        self.Ruca.run()


###########################################################################
    def on_inicializa(self, button):

        if self.confirm_action(
            "Confirmar inicialización",
            "¿Desea inicializar las ruedas? Esta acción puede mover los mecanismos."
        ):
            print("Inicializando ruedas")
            self.Ruca.inicializa()


    # =============================================
    def on_main_notebook_switch_page(self, notebook, page, page_num):

        if self.restoring_notebook_page:
            self.restoring_notebook_page = False
            self.previous_notebook_page = page_num
            return

        if page == self.help_page:
            self.load_help_markdown()

        if page == self.engineering_page and not self.engineering_access_authorized:
            authorized = self.confirm_action(
                "Acceso restringido",
                (
                    "La pestaña Ingeniería es de uso exclusivo del personal "
                    "técnico académico de soporte. ¿Desea continuar?"
                )
            )

            if not authorized:
                self.restoring_notebook_page = True
                GLib.idle_add(
                    notebook.set_current_page,
                    self.previous_notebook_page
                )
                return

            self.engineering_access_authorized = True

        self.previous_notebook_page = page_num


    # =============================================
    def configure_help_view(self):

        buffer = self.help_text_view.get_buffer()
        buffer.create_tag(
            "heading1",
            weight=Pango.Weight.BOLD,
            scale=1.5,
            pixels_above_lines=12,
            pixels_below_lines=8
        )
        buffer.create_tag(
            "heading2",
            weight=Pango.Weight.BOLD,
            scale=1.25,
            pixels_above_lines=10,
            pixels_below_lines=6
        )
        buffer.create_tag(
            "heading3",
            weight=Pango.Weight.BOLD,
            scale=1.1,
            pixels_above_lines=8,
            pixels_below_lines=4
        )
        buffer.create_tag(
            "list",
            left_margin=18,
            indent=-12,
            pixels_below_lines=3
        )
        buffer.create_tag(
            "code",
            family="monospace",
            background="#eeeeee",
            left_margin=18,
            right_margin=18,
            pixels_above_lines=4,
            pixels_below_lines=4
        )
        buffer.create_tag("body", pixels_below_lines=4)
        buffer.create_tag(
            "error",
            foreground="#b00020",
            weight=Pango.Weight.BOLD
        )
        self.load_help_markdown()


    # =============================================
    def load_help_markdown(self):

        buffer = self.help_text_view.get_buffer()
        buffer.set_text("")

        try:
            with open("AYUDA.md", "r", encoding="utf-8") as help_file:
                markdown = help_file.read()
        except (OSError, UnicodeError) as error:
            self.insert_help_text(
                buffer,
                (
                    "No fue posible cargar AYUDA.md.\n\n"
                    f"Detalle: {error}"
                ),
                "error"
            )
            return

        in_code_block = False

        for line in markdown.splitlines():
            stripped = line.strip()

            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                self.insert_help_text(buffer, line + "\n", "code")
            elif line.startswith("### "):
                self.insert_help_text(buffer, line[4:] + "\n", "heading3")
            elif line.startswith("## "):
                self.insert_help_text(buffer, line[3:] + "\n", "heading2")
            elif line.startswith("# "):
                self.insert_help_text(buffer, line[2:] + "\n", "heading1")
            elif line.startswith("- "):
                self.insert_help_text(buffer, "• " + line[2:] + "\n", "list")
            elif stripped:
                self.insert_help_text(buffer, line + "\n", "body")
            else:
                self.insert_help_text(buffer, "\n", "body")

        buffer.place_cursor(buffer.get_start_iter())


    # =============================================
    def insert_help_text(self, buffer, text, tag_name):

        buffer.insert_with_tags_by_name(
            buffer.get_end_iter(),
            text,
            tag_name
        )


    # =============================================
    def on_engineering_speed(self, button):

        speed_text = self.engineering_speed.get_text().strip()

        try:
            speed = int(speed_text)
        except ValueError:
            self.set_engineering_status(
                "La velocidad debe ser un número entero",
                error=True
            )
            return

        if not 1 <= speed <= 100:
            self.set_engineering_status(
                "La velocidad debe estar entre 1 y 100 RPM",
                error=True
            )
            return

        self.send_engineering_command(f"SPEED {speed}", speed)


    # =============================================
    def on_engineering_stop(self, button):

        if self.confirm_action(
            "Confirmar STOP",
            "¿Desea detener y bloquear la rueda?"
        ):
            self.send_engineering_command("STOP")


    # =============================================
    def on_engineering_inicio(self, button):

        if self.confirm_action(
            "Confirmar INICIO",
            "¿Desea iniciar la búsqueda de posición inicial?"
        ):
            self.send_engineering_command("INICIO")


    # =============================================
    def on_engineering_state(self, button):

        self.request_direct_state()


    # =============================================
    def on_engineering_apply_brakes(self, button):

        self.send_engineering_command("FRENOS 1")


    # =============================================
    def on_engineering_release_brakes(self, button):

        if self.confirm_action(
            "Confirmar liberación de frenos",
            "¿Desea liberar los frenos de los tres mecanismos?"
        ):
            self.send_engineering_command("FRENOS 0")


    # =============================================
    def on_engineering_move(self, button):

        motor = self.engineering_move_motor.get_active_id()
        direction = self.engineering_move_direction.get_active_id()
        steps_text = self.engineering_move_steps.get_text().strip()

        try:
            steps = int(steps_text)
        except ValueError:
            self.set_engineering_status(
                "Los pasos deben ser un número entero",
                error=True
            )
            return

        if motor not in ("1", "2", "3") or direction not in ("0", "1"):
            self.set_engineering_status(
                "Seleccione un motor y una dirección válidos",
                error=True
            )
            return

        if not 1 <= steps <= 500:
            self.set_engineering_status(
                "Los pasos deben estar entre 1 y 500",
                error=True
            )
            return

        motor_name = {
            "1": "Rueda",
            "2": "Polarizador",
            "3": "Reductor",
        }[motor]
        direction_name = "Adelante" if direction == "1" else "Atrás"

        if self.confirm_action(
            "Confirmar movimiento manual",
            f"{motor_name}: {steps} pasos hacia {direction_name}"
        ):
            self.send_engineering_command(
                f"MUEVE {motor} {steps} {direction}"
            )


    # =============================================
    def confirm_action(self, title, message):

        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=title
        )
        dialog.format_secondary_text(message)
        response = dialog.run()
        dialog.destroy()

        return response == Gtk.ResponseType.OK


    # =============================================
    def send_engineering_command(self, command, requested_speed=None):

        endpoint = self.get_engineering_endpoint()

        if endpoint is None:
            return

        host, port = endpoint
        self.engineering_controls.set_sensitive(False)
        self.set_engineering_status(f"Enviando {command}...")

        self.Ruca.envia_comando_tcp(
            host,
            port,
            command,
            lambda ok, response: GLib.idle_add(
                self.on_engineering_response,
                ok,
                response,
                requested_speed,
                command
            )
        )


    # =============================================
    def on_engineering_response(self, ok, response, requested_speed, command):

        accepted = ok and not response.upper().startswith("ERROR")
        self.set_engineering_status(response, error=not accepted)

        if (
            accepted
            and requested_speed is not None
            and response.upper().startswith("OK:")
        ):
            self.engineering_current_speed.set_text(str(requested_speed))

        if accepted:
            self.request_direct_state(
                command_message=response,
                keep_controls_disabled=True
            )
        else:
            self.engineering_controls.set_sensitive(True)
            self.set_direct_connection(False, "Error de comando")

        return False


    # =============================================
    def request_direct_state(
        self,
        command_message=None,
        keep_controls_disabled=False
    ):

        endpoint = self.get_engineering_endpoint()

        if endpoint is None:
            self.engineering_controls.set_sensitive(True)
            return

        host, port = endpoint

        if not keep_controls_disabled:
            self.engineering_controls.set_sensitive(False)

        self.set_direct_connection(False, "Consultando...")
        self.set_engineering_status(
            command_message or "Solicitando ESTADO directo..."
        )

        self.Ruca.envia_comando_tcp(
            host,
            port,
            "ESTADO",
            lambda ok, response: GLib.idle_add(
                self.on_direct_state_response,
                ok,
                response,
                command_message
            ),
            conservar_respuesta_completa=True
        )


    # =============================================
    def on_direct_state_response(self, ok, response, command_message):

        self.engineering_controls.set_sensitive(True)

        if not ok:
            self.set_direct_connection(False, "Sin comunicación")
            self.set_engineering_status(
                (
                    f"{command_message} | ESTADO: {response}"
                    if command_message
                    else response
                ),
                error=True
            )
            return False

        try:
            state = json.loads(response)
        except (TypeError, ValueError):
            self.set_direct_connection(False, "JSON inválido")
            self.set_engineering_status(
                "El servidor respondió ESTADO con JSON inválido",
                error=True
            )
            return False

        self.populate_engineering_state(state)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.set_direct_connection(True, "Conectado")
        self.engineering_last_update.set_text(f"Última lectura: {now}")
        self.set_engineering_status(command_message or "ESTADO actualizado")

        return False


    # =============================================
    def get_engineering_endpoint(self):

        host = self.engineering_host.get_text().strip()
        port_text = self.engineering_port.get_text().strip()

        if not host:
            self.set_engineering_status("La dirección IP es obligatoria", True)
            return None

        try:
            port = int(port_text)
        except ValueError:
            self.set_engineering_status("El puerto debe ser numérico", True)
            return None

        if not 1 <= port <= 65535:
            self.set_engineering_status(
                "El puerto debe estar entre 1 y 65535",
                True
            )
            return None

        return host, port


    # =============================================
    def add_engineering_state_column(self, title, model_index):

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(
            title,
            renderer,
            text=model_index,
            foreground=3,
            weight=4
        )
        column.set_resizable(True)
        column.set_expand(True)
        self.engineering_state_tree.append_column(column)


    # =============================================
    def populate_engineering_state(self, state):

        self.engineering_state_model.clear()

        for section, variables in self.ENGINEERING_STATE_SECTIONS:
            self.engineering_state_model.append([
                section,
                section,
                "",
                "#444444",
                int(Pango.Weight.BOLD),
            ])

            for variable in variables:
                value = state.get(variable, "--")
                color, weight = self.get_engineering_value_style(
                    variable,
                    value
                )
                self.engineering_state_model.append([
                    section,
                    variable,
                    str(value),
                    color,
                    weight,
                ])


    # =============================================
    def get_engineering_value_style(self, variable, value):

        if variable in self.ENGINEERING_BLUE_VALUES:
            return "#174ea6", int(Pango.Weight.BOLD)

        if variable == "RUEDA_ESTADO":
            if "ERROR" in str(value).upper():
                return "#b00020", int(Pango.Weight.BOLD)
            return "#137333", int(Pango.Weight.BOLD)

        if variable == "RUEDA_PARO_EMERGENCIA":
            if value in (1, "1", True):
                return "#b00020", int(Pango.Weight.BOLD)
            return "#137333", int(Pango.Weight.NORMAL)

        if variable.startswith("FIRST_INIT_"):
            if value in (1, "1", True):
                return "#137333", int(Pango.Weight.BOLD)
            return "#b06000", int(Pango.Weight.BOLD)

        if variable.endswith("_FRENO_SENSOR"):
            if value in (1, "1", True):
                return "#b06000", int(Pango.Weight.BOLD)
            return "#137333", int(Pango.Weight.NORMAL)

        return "#333333", int(Pango.Weight.NORMAL)


    # =============================================
    def set_direct_connection(self, connected, text):

        self.engineering_connection.set_text(text)
        color = "darkgreen" if connected else "red"
        self.engineering_connection.modify_fg(
            Gtk.StateFlags.NORMAL,
            Gdk.color_parse(color)
        )


    # =============================================
    def set_engineering_status(self, message, error=False):

        self.engineering_status.set_text(message)
        color = "red" if error else "darkgreen"
        self.engineering_status.modify_fg(
            Gtk.StateFlags.NORMAL,
            Gdk.color_parse(color)
        )


    # =============================================
    def on_recargar_filtros(self, button):

        if not self.confirm_action(
            "Confirmar publicación de filtros",
            "¿Desea releer los archivos y publicar la lista de filtros por MQTT?"
        ):
            return

        print("Publicando lista de filtros")

        self.Ruca.recargar_filtros()

        self.actualiza_lista_filtros()


    # =============================================
    def actualiza_lista_filtros(self):

        actual = self.c_filtros.get_active()

        self.c_filtros.handler_block_by_func(
            self.on_filtros_combo_changed
        )

        self.lfiltros.clear()

        for d in self.Ruca.lista_filtros:
            self.lfiltros.append([d])

        if actual >= 0:
            self.c_filtros.set_active(actual)
        else:
            self.c_filtros.set_active(0)

        self.c_filtros.handler_unblock_by_func(
            self.on_filtros_combo_changed
        )


    # =============================================
    def on_filtros_combo_changed(self, combo):

        index = combo.get_active()

        if index >= 0:

            self.Ruca.mueve_filtros(index + 1)


    # =============================================
    def c_reductor_changed(self, widget, data=None):

        index = widget.get_active()

        if index >= 0:

            self.Ruca.mueve_reductor(index + 1)


    # =============================================
    def salida(self, *args):

        print("Cerrando")

        Gtk.main_quit()


    # =============================================
    def carga_datos_ui(self, info):

        GLib.idle_add(self.pinta_datos_gui)


    def pinta_datos_gui(self):

        try:

            info = self.Ruca.info


            # ---------- FILTRO ----------
            i = info.get("RUEDA_INDICE", 1)

            if 1 <= i <= len(self.Ruca.lista_filtros):

                nombre = self.Ruca.lista_filtros[i-1]

            else:

                nombre = "?"


            self.e_filtro.set_text(nombre)


            # ---------- SWITCH ----------
            if info.get("RUEDA_SWITCH", 0) == 1:

                self.e_switch.set_text("IN")

                self.e_switch.modify_bg(
                    Gtk.StateFlags.NORMAL,
                    Gdk.color_parse("lightgreen")
                )

            else:

                self.e_switch.set_text("OUT")

                self.e_switch.modify_bg(
                    Gtk.StateFlags.NORMAL,
                    Gdk.color_parse("red")
                )


            # ---------- ESTADO ----------
            estado = info.get("RUEDA_ESTADO", "N/A")

            self.e_estado.set_text(str(estado))

            speed = info.get("RUEDA_SPEED")

            if speed is not None:
                self.engineering_current_speed.set_text(str(speed))


        except Exception as e:

            print("Error GUI:", e)



# =================================================
def main():

    app = MainApp()

    Gtk.main()


if __name__ == "__main__":

    main()
