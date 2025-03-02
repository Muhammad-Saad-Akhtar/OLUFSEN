import dearpygui.dearpygui as dpg

dpg.create_context()

def neon_theme():
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (10, 10, 20, 240))  # Dark blue background
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 255, 255, 255))  # Neon cyan text
            dpg.add_theme_color(dpg.mvThemeCol_Button, (255, 0, 255, 180))  # Magenta buttons
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 20, 147, 220))  # Bright hover
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (255, 105, 180, 255))  # Active button
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)  # Rounded buttons
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 10)  # Increased spacing
    return global_theme

def send_message_callback(sender, app_data, user_input_id):
    message = dpg.get_value(user_input_id)
    if message.strip():
        print("Message Sent:", message)
        dpg.set_value(user_input_id, "")  # Clear input field

def chatbot_ui():
    with dpg.window(label="OLUFSEN - Cyberpunk AI", width=800, height=600, pos=(100, 100)) as main_window:
        dpg.add_text("Welcome to OLUFSEN!", color=(0, 255, 255, 255), bullet=True, wrap=600)
        dpg.add_separator()
        dpg.add_text("AI Response will appear here", color=(255, 255, 0, 255), wrap=600)
        dpg.add_separator()
        with dpg.group(horizontal=False):
            user_input_id = dpg.add_input_text(label="User Input", width=600)
            dpg.add_button(label="Send", callback=lambda: send_message_callback(None, None, user_input_id))
        dpg.set_item_callback(user_input_id, lambda sender, app_data: send_message_callback(sender, app_data, user_input_id))
        dpg.bind_item_theme(main_window, neon_theme())
    return main_window

dpg.create_viewport(title="OLUFSEN - AI Chatbot", width=1000, height=700)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window(chatbot_ui(), True)
dpg.start_dearpygui()
dpg.destroy_context()
