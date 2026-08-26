import customtkinter as ctk


class AppState:
    """Plain holder for everything the main window's widgets are bound to. A single instance is
    created by MainGUIController and passed through build_layout()/configure_handlers() so both
    stay in sync without module-level globals; layout_builder also attaches widget references
    directly onto this same object as it builds them (e.g. state.solve_button)."""
    def __init__(self, root):
        self.agent_list = []

        self.map_var = ctk.StringVar(master=root)
        self.k_var = ctk.StringVar(master=root)
        self.h_var = ctk.StringVar(master=root)
        self.m_var = ctk.StringVar(master=root)

        self.map_gen_var = ctk.StringVar(master=root)
        self.num_instances_var = ctk.StringVar(master=root)
        self.num_agents_var = ctk.StringVar(master=root)
        self.min_dist_var = ctk.StringVar(master=root)
        self.name_set_var = ctk.StringVar(master=root)

        self.fail_type_vars = {
            "topw": ctk.BooleanVar(master=root),
            "tops": ctk.BooleanVar(master=root),
            "individual": ctk.BooleanVar(master=root),
            "high-level": ctk.BooleanVar(master=root),
        }