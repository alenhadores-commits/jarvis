#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================
   J.A.R.V.I.S — NÚCLEO LOCAL (DESKTOP)
   Interface gráfica em Python (tkinter)
   Inspirada no protótipo web (HTML/CSS/JS)
==========================================

Requisitos:
    - Python 3.9+ (testado com tkinter da biblioteca padrão)
    - Opcional: psutil (para CPU/RAM reais)  ->  pip install psutil
    - Opcional: pyttsx3 (para voz)           ->  pip install pyttsx3

Este arquivo é o "esqueleto" da interface do Alfred/J.A.R.V.I.S:
mantém o formato central (o núcleo/orb animado) e o chat do
protótipo original, e adiciona um visual futurista ao redor
(painel de sistema, atividade em tempo real, agenda e memória).

A lógica de comandos (process_command) é o ponto onde depois se
pluga o "cérebro" real do Alfred (controle de pastas, mouse,
teclado, leitura de tela etc.) — hoje ela só interpreta um punhado
de comandos locais para a interface já nascer funcional.
"""

import math
import os
import platform
import random
import subprocess
import sys
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import font as tkfont

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ==========================================
# PALETA / TEMA
# ==========================================

class Theme:
    BG = "#05070d"
    BG_PANEL = "#0b0f1a"
    BG_PANEL_2 = "#0e1422"
    BORDER = "#1c2438"
    CYAN = "#28e0ff"
    CYAN_DIM = "#0f7c99"
    PURPLE = "#8b5cf6"
    GREEN = "#37e6a0"
    RED = "#ff5f6d"
    AMBER = "#ffb454"
    TEXT = "#e7f6ff"
    TEXT_DIM = "#7f93b3"
    TEXT_FAINT = "#3f4b63"

    FONT_FAMILY = "Segoe UI" if platform.system() == "Windows" else "Helvetica"
    FONT_MONO = "Consolas" if platform.system() == "Windows" else "Courier"


# Estados do núcleo (espelha o "estados" do app.js original)
STATES = {
    "listening": ("OUVINDO", "Estou ouvindo você", Theme.GREEN),
    "thinking": ("PENSANDO", "Processando seu comando", Theme.PURPLE),
    "speaking": ("FALANDO", "Preparando resposta", Theme.CYAN),
    "executing": ("EXECUTANDO", "Realizando tarefa", Theme.AMBER),
    "attention": ("ATENÇÃO", "Preciso da sua atenção", Theme.RED),
    "ready": ("PRONTO", "Aguardando comando", Theme.CYAN),
}


# ==========================================
# NÚCLEO VISUAL (ORB) — Canvas animado
# ==========================================

class CoreOrb(tk.Canvas):
    """O 'núcleo' central: anéis girando + esfera pulsante.
    Mantém o mesmo papel do .orb / .orb-ring do protótipo web."""

    SIZE = 260

    def __init__(self, master, **kw):
        super().__init__(
            master, width=self.SIZE, height=self.SIZE,
            bg=Theme.BG, highlightthickness=0, **kw
        )
        self.cx = self.SIZE / 2
        self.cy = self.SIZE / 2
        self.angle = 0.0
        self.pulse_t = 0.0
        self.color = Theme.CYAN
        self._running = True
        self._tick()

    def set_color(self, color):
        self.color = color

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running:
            return
        self.angle = (self.angle + 2.4) % 360
        self.pulse_t += 0.12
        self._draw()
        self.after(33, self._tick)  # ~30 fps

    def _draw(self):
        self.delete("all")
        pulse = (math.sin(self.pulse_t) + 1) / 2  # 0..1

        # três anéis concêntricos, cada um girando numa "fase" diferente
        radii = [110, 85, 60]
        widths = [1, 2, 3]
        for i, r in enumerate(radii):
            start = (self.angle * (1 + i * 0.6)) % 360
            extent = 110 - i * 15
            self.create_arc(
                self.cx - r, self.cy - r, self.cx + r, self.cy + r,
                start=start, extent=extent,
                outline=self.color, width=widths[i], style="arc"
            )
            self.create_arc(
                self.cx - r, self.cy - r, self.cx + r, self.cy + r,
                start=start + 180, extent=extent,
                outline=self.color, width=widths[i], style="arc"
            )

        # núcleo pulsante (glow simulado com círculos sobrepostos)
        core_r = 22 + pulse * 6
        for k, alpha_r in enumerate([core_r + 18, core_r + 9, core_r]):
            shade = self._blend_with_bg(self.color, 0.15 + k * 0.25)
            self.create_oval(
                self.cx - alpha_r, self.cy - alpha_r,
                self.cx + alpha_r, self.cy + alpha_r,
                outline="", fill=shade
            )
        self.create_oval(
            self.cx - 8, self.cy - 8, self.cx + 8, self.cy + 8,
            outline="", fill=Theme.TEXT
        )

        # pequenas partículas orbitando (satélites)
        for i in range(3):
            a = math.radians(self.angle * 1.7 + i * 120)
            px = self.cx + math.cos(a) * 130
            py = self.cy + math.sin(a) * 130
            self.create_oval(px - 2, py - 2, px + 2, py + 2, fill=self.color, outline="")

    @staticmethod
    def _blend_with_bg(hex_color, factor):
        """Escurece a cor em direção ao fundo, simulando opacidade/glow."""
        bg = Theme.BG.lstrip("#")
        col = hex_color.lstrip("#")
        bg_rgb = tuple(int(bg[i:i + 2], 16) for i in (0, 2, 4))
        col_rgb = tuple(int(col[i:i + 2], 16) for i in (0, 2, 4))
        blended = tuple(
            int(bg_rgb[i] + (col_rgb[i] - bg_rgb[i]) * factor) for i in range(3)
        )
        return "#%02x%02x%02x" % blended


# ==========================================
# FUNDO DE PARTÍCULAS
# ==========================================

class ParticleField(tk.Canvas):
    """Poeira estelar subindo lentamente no fundo — o equivalente
    ao #particles do CSS original, feito em canvas."""

    def __init__(self, master, count=45, **kw):
        super().__init__(master, bg=Theme.BG, highlightthickness=0, **kw)
        self.particles = []
        self.count = count
        self.bind("<Configure>", self._on_resize)
        self._seeded = False
        self._running = True
        self._tick()

    def _on_resize(self, event):
        if not self._seeded and event.width > 10 and event.height > 10:
            self._seed(event.width, event.height)
            self._seeded = True

    def _seed(self, w, h):
        self.particles = []
        for _ in range(self.count):
            self.particles.append({
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "r": random.uniform(1, 2.4),
                "speed": random.uniform(0.15, 0.6),
                "alpha": random.uniform(0.15, 0.6),
            })

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running:
            return
        w = self.winfo_width()
        h = self.winfo_height()
        if w > 10 and h > 10 and self.particles:
            self.delete("all")
            for p in self.particles:
                p["y"] -= p["speed"]
                if p["y"] < -5:
                    p["y"] = h + 5
                    p["x"] = random.uniform(0, w)
                shade = ParticleField._shade(p["alpha"])
                self.create_oval(
                    p["x"] - p["r"], p["y"] - p["r"],
                    p["x"] + p["r"], p["y"] + p["r"],
                    outline="", fill=shade
                )
        self.after(45, self._tick)

    @staticmethod
    def _shade(alpha):
        bg = Theme.BG.lstrip("#")
        bg_rgb = tuple(int(bg[i:i + 2], 16) for i in (0, 2, 4))
        cyan_rgb = tuple(int(Theme.CYAN.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        blended = tuple(int(bg_rgb[i] + (cyan_rgb[i] - bg_rgb[i]) * alpha) for i in range(3))
        return "#%02x%02x%02x" % blended


# ==========================================
# APLICAÇÃO PRINCIPAL
# ==========================================

class JarvisApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("J.A.R.V.I.S — Núcleo Local")
        self.geometry("1280x760")
        self.minsize(1040, 640)
        self.configure(bg=Theme.BG)

        self.state_name = "ready"
        self.activity_items = []  # lista de (texto, cor, hora)

        self._build_fonts()
        self._build_layout()
        self._update_clock()
        self._update_system()
        self._log_activity("Núcleo iniciado", Theme.CYAN)
        self._add_message("Interface online. Núcleo local aguardando comando.", "assistant")

    # ---------- fontes ----------
    def _build_fonts(self):
        f = Theme.FONT_FAMILY
        self.f_title = tkfont.Font(family=f, size=15, weight="bold")
        self.f_subtitle = tkfont.Font(family=f, size=8)
        self.f_state = tkfont.Font(family=f, size=20, weight="bold")
        self.f_desc = tkfont.Font(family=f, size=10)
        self.f_body = tkfont.Font(family=f, size=10)
        self.f_bold = tkfont.Font(family=f, size=10, weight="bold")
        self.f_small = tkfont.Font(family=f, size=8)
        self.f_mono = tkfont.Font(family=Theme.FONT_MONO, size=11)

    # ---------- layout geral ----------
    def _build_layout(self):
        self._build_topbar()

        body = tk.Frame(self, bg=Theme.BG)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_main(body)
        self._build_right_panel(body)

    # ---------- topo ----------
    def _build_topbar(self):
        top = tk.Frame(self, bg=Theme.BG_PANEL, height=56)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        brand = tk.Frame(top, bg=Theme.BG_PANEL)
        brand.pack(side="left", padx=18)
        orb_dot = tk.Canvas(brand, width=28, height=28, bg=Theme.BG_PANEL, highlightthickness=0)
        orb_dot.pack(side="left", padx=(0, 10))
        orb_dot.create_oval(4, 4, 24, 24, outline=Theme.CYAN, width=2)
        orb_dot.create_oval(11, 11, 17, 17, fill=Theme.CYAN, outline="")

        txt = tk.Frame(brand, bg=Theme.BG_PANEL)
        txt.pack(side="left")
        tk.Label(txt, text="J.A.R.V.I.S", font=self.f_title, fg=Theme.TEXT, bg=Theme.BG_PANEL).pack(anchor="w")
        tk.Label(txt, text="PERSONAL INTELLIGENCE SYSTEM", font=self.f_subtitle,
                 fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL).pack(anchor="w")

        status = tk.Frame(top, bg=Theme.BG_PANEL)
        status.pack(side="right", padx=18)

        self.connection_label = tk.Label(
            status, text="●  ONLINE", font=self.f_small, fg=Theme.GREEN, bg=Theme.BG_PANEL
        )
        self.connection_label.pack(side="left", padx=12)

        self.clock_label = tk.Label(status, text="00:00:00", font=self.f_mono, fg=Theme.TEXT, bg=Theme.BG_PANEL)
        self.clock_label.pack(side="left", padx=12)

        tk.Button(
            status, text="⚙", font=self.f_body, fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL,
            activebackground=Theme.BG_PANEL_2, bd=0, relief="flat", cursor="hand2",
            command=lambda: self._log_activity("Configurações ainda não conectadas", Theme.PURPLE)
        ).pack(side="left", padx=6)

    # ---------- sidebar ----------
    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=Theme.BG_PANEL, width=210)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        tk.Label(side, text="SYSTEM", font=self.f_small, fg=Theme.TEXT_FAINT,
                 bg=Theme.BG_PANEL).pack(anchor="w", padx=16, pady=(18, 6))

        nav_items = [
            ("◉", "Comando", "Central"),
            ("🧠", "Memória", "Conhecimento"),
            ("📅", "Agenda", "Compromissos"),
            ("⚡", "Habilidades", "Skills"),
            ("📁", "Arquivos", "Computador"),
        ]
        for icon, title, sub in nav_items:
            self._nav_button(side, icon, title, sub)

        tk.Frame(side, bg=Theme.BORDER, height=1).pack(fill="x", padx=16, pady=14)
        tk.Label(side, text="HOJE", font=self.f_small, fg=Theme.TEXT_FAINT,
                 bg=Theme.BG_PANEL).pack(anchor="w", padx=16, pady=(0, 6))

        self._mini_info(side, "◷", Theme.CYAN, "Agenda", "Compromissos de hoje")
        self._mini_info(side, "✦", Theme.PURPLE, "3 tarefas", "Pendentes")
        self._mini_info(side, "✓", Theme.GREEN, "Sistema", "Funcionando")

        bottom = tk.Frame(side, bg=Theme.BG_PANEL)
        bottom.pack(side="bottom", fill="x", pady=16, padx=16)
        avatar = tk.Label(bottom, text="U", font=self.f_bold, fg=Theme.BG,
                           bg=Theme.CYAN, width=3, height=1)
        avatar.pack(side="left")
        info = tk.Frame(bottom, bg=Theme.BG_PANEL)
        info.pack(side="left", padx=8)
        tk.Label(info, text="Usuário", font=self.f_bold, fg=Theme.TEXT, bg=Theme.BG_PANEL).pack(anchor="w")
        tk.Label(info, text="Administrador", font=self.f_small, fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL).pack(anchor="w")

    def _nav_button(self, parent, icon, title, sub):
        btn = tk.Frame(parent, bg=Theme.BG_PANEL, cursor="hand2")
        btn.pack(fill="x", padx=10, pady=2)
        inner = tk.Frame(btn, bg=Theme.BG_PANEL)
        inner.pack(fill="x", padx=6, pady=6)
        tk.Label(inner, text=icon, font=self.f_body, fg=Theme.CYAN, bg=Theme.BG_PANEL).pack(side="left", padx=(0, 8))
        col = tk.Frame(inner, bg=Theme.BG_PANEL)
        col.pack(side="left")
        tk.Label(col, text=title, font=self.f_bold, fg=Theme.TEXT, bg=Theme.BG_PANEL).pack(anchor="w")
        tk.Label(col, text=sub, font=self.f_small, fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL).pack(anchor="w")

        def on_click(_e=None, t=title):
            self._log_activity(f"Painel '{t}' ainda não conectado", Theme.PURPLE)

        for widget in (btn, inner, col):
            widget.bind("<Button-1>", on_click)

    def _mini_info(self, parent, icon, color, title, sub):
        row = tk.Frame(parent, bg=Theme.BG_PANEL)
        row.pack(fill="x", padx=16, pady=4)
        tk.Label(row, text=icon, font=self.f_body, fg=color, bg=Theme.BG_PANEL).pack(side="left", padx=(0, 8))
        col = tk.Frame(row, bg=Theme.BG_PANEL)
        col.pack(side="left")
        tk.Label(col, text=title, font=self.f_bold, fg=Theme.TEXT, bg=Theme.BG_PANEL).pack(anchor="w")
        tk.Label(col, text=sub, font=self.f_small, fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL).pack(anchor="w")

    # ---------- centro (núcleo + chat) ----------
    def _build_main(self, parent):
        main = tk.Frame(parent, bg=Theme.BG)
        main.pack(side="left", fill="both", expand=True)

        # --- hero / núcleo central ---
        hero_wrap = tk.Frame(main, bg=Theme.BG, height=340)
        hero_wrap.pack(fill="x")
        hero_wrap.pack_propagate(False)

        self.particles = ParticleField(hero_wrap, count=40)
        self.particles.place(x=0, y=0, relwidth=1, relheight=1)

        hero_center = tk.Frame(hero_wrap, bg=Theme.BG)
        hero_center.place(relx=0.5, rely=0.46, anchor="center")

        self.orb = CoreOrb(hero_center, bg=Theme.BG)
        self.orb.pack()

        self.state_label = tk.Label(hero_center, text=STATES["ready"][0], font=self.f_state,
                                     fg=Theme.CYAN, bg=Theme.BG)
        self.state_label.pack(pady=(6, 0))
        self.desc_label = tk.Label(hero_center, text=STATES["ready"][1], font=self.f_desc,
                                    fg=Theme.TEXT_DIM, bg=Theme.BG)
        self.desc_label.pack()

        quick = tk.Frame(hero_center, bg=Theme.BG)
        quick.pack(pady=12)
        self._quick_button(quick, "🎙️ Voz", self._quick_voice)
        self._quick_button(quick, "⚡ Executar", self._quick_execute)
        self._quick_button(quick, "🧠 Memória", self._quick_memory)

        # --- chat ---
        chat_area = tk.Frame(main, bg=Theme.BG_PANEL)
        chat_area.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        chat_title = tk.Frame(chat_area, bg=Theme.BG_PANEL)
        chat_title.pack(fill="x", padx=14, pady=(12, 6))
        left_t = tk.Frame(chat_title, bg=Theme.BG_PANEL)
        left_t.pack(side="left")
        tk.Label(left_t, text="●", font=self.f_small, fg=Theme.GREEN, bg=Theme.BG_PANEL).pack(side="left")
        tk.Label(left_t, text=" CONVERSA", font=self.f_bold, fg=Theme.TEXT, bg=Theme.BG_PANEL).pack(side="left")
        tk.Label(left_t, text="   Canal principal", font=self.f_small, fg=Theme.TEXT_DIM,
                 bg=Theme.BG_PANEL).pack(side="left")
        tk.Button(chat_title, text="Limpar", font=self.f_small, fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL_2,
                  activebackground=Theme.BORDER, bd=0, relief="flat", cursor="hand2", padx=10, pady=4,
                  command=self._clear_chat).pack(side="right")

        chat_body = tk.Frame(chat_area, bg=Theme.BG_PANEL_2)
        chat_body.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.chat_text = tk.Text(
            chat_body, bg=Theme.BG_PANEL_2, fg=Theme.TEXT, font=self.f_body,
            wrap="word", bd=0, padx=12, pady=10, state="disabled", cursor="arrow"
        )
        scrollbar = tk.Scrollbar(chat_body, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        self.chat_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.chat_text.tag_configure("name_user", foreground=Theme.CYAN, font=self.f_bold)
        self.chat_text.tag_configure("name_assistant", foreground=Theme.PURPLE, font=self.f_bold)
        self.chat_text.tag_configure("body", foreground=Theme.TEXT, font=self.f_body)
        self.chat_text.tag_configure("spacer", font=self.f_small)

        # --- barra de comando ---
        cmd_area = tk.Frame(chat_area, bg=Theme.BG_PANEL)
        cmd_area.pack(fill="x", padx=14, pady=(0, 12))

        cmd_box = tk.Frame(cmd_area, bg=Theme.BG_PANEL_2, bd=1, relief="solid")
        cmd_box.pack(fill="x")
        cmd_box.configure(highlightbackground=Theme.BORDER, highlightthickness=1, bd=0)

        self.mic_btn = tk.Button(
            cmd_box, text="🎙️", font=self.f_body, fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL_2,
            activebackground=Theme.BORDER, bd=0, relief="flat", cursor="hand2",
            command=self._mic_click
        )
        self.mic_btn.pack(side="left", padx=8, pady=8)

        self.entry = tk.Entry(
            cmd_box, bg=Theme.BG_PANEL_2, fg=Theme.TEXT, insertbackground=Theme.TEXT,
            font=self.f_body, bd=0, relief="flat"
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=6)
        self.entry.insert(0, "")
        self.entry.bind("<Return>", lambda e: self._send_command())
        self._set_placeholder()

        self.send_btn = tk.Button(
            cmd_box, text="➤", font=self.f_body, fg=Theme.BG, bg=Theme.CYAN,
            activebackground=Theme.CYAN_DIM, bd=0, relief="flat", cursor="hand2",
            command=self._send_command, padx=14
        )
        self.send_btn.pack(side="right", padx=8, pady=8)

        footer = tk.Frame(cmd_area, bg=Theme.BG_PANEL)
        footer.pack(fill="x", pady=(6, 0))

        modes = tk.Frame(footer, bg=Theme.BG_PANEL)
        modes.pack(side="left")
        self.mode_chat_btn = tk.Button(
            modes, text="💬 CHAT", font=self.f_small, fg=Theme.BG, bg=Theme.CYAN, bd=0,
            relief="flat", cursor="hand2", padx=10, pady=4, command=self._mode_chat
        )
        self.mode_chat_btn.pack(side="left", padx=(0, 6))
        self.mode_voice_btn = tk.Button(
            modes, text="🎙️ VOZ", font=self.f_small, fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL_2, bd=0,
            relief="flat", cursor="hand2", padx=10, pady=4, command=self._mode_voice
        )
        self.mode_voice_btn.pack(side="left")

        tk.Label(footer, text="ENTER para enviar", font=self.f_small, fg=Theme.TEXT_FAINT,
                 bg=Theme.BG_PANEL).pack(side="right")

    def _quick_button(self, parent, text, cmd):
        b = tk.Button(
            parent, text=text, font=self.f_small, fg=Theme.TEXT, bg=Theme.BG_PANEL_2,
            activebackground=Theme.BORDER, bd=1, relief="solid", cursor="hand2",
            padx=12, pady=6, command=cmd
        )
        b.configure(highlightbackground=Theme.BORDER)
        b.pack(side="left", padx=6)
        return b

    # ---------- painel direito ----------
    def _build_right_panel(self, parent):
        panel = tk.Frame(parent, bg=Theme.BG, width=280)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        # -- sistema --
        card = self._panel_card(panel, "SYSTEM", dot_color=Theme.GREEN)
        self.cpu_bar, self.cpu_val = self._system_row(card, "CPU", Theme.CYAN)
        self.ram_bar, self.ram_val = self._system_row(card, "RAM", Theme.PURPLE)

        net_row = tk.Frame(card, bg=Theme.BG_PANEL)
        net_row.pack(fill="x", pady=(8, 4))
        tk.Label(net_row, text="NETWORK", font=self.f_small, fg=Theme.TEXT_DIM,
                 bg=Theme.BG_PANEL).pack(side="left")
        self.network_label = tk.Label(net_row, text="● CONECTADO", font=self.f_small,
                                       fg=Theme.GREEN, bg=Theme.BG_PANEL)
        self.network_label.pack(side="right")

        # -- atividade --
        act_card = self._panel_card(panel, "ATIVIDADE", dot_color=Theme.CYAN, right_text="● LIVE")
        self.activity_frame = tk.Frame(act_card, bg=Theme.BG_PANEL)
        self.activity_frame.pack(fill="both", expand=True, pady=4)

        # -- próximo compromisso --
        appt_card = self._panel_card(panel, "PRÓXIMO COMPROMISSO")
        tk.Label(appt_card, text="--:--", font=self.f_state, fg=Theme.TEXT,
                 bg=Theme.BG_PANEL).pack(anchor="w", pady=(4, 0))
        tk.Label(appt_card, text="Nenhum carregado", font=self.f_bold, fg=Theme.TEXT_DIM,
                 bg=Theme.BG_PANEL).pack(anchor="w")
        tk.Label(appt_card, text="Agenda será integrada depois", font=self.f_small, fg=Theme.TEXT_FAINT,
                 bg=Theme.BG_PANEL).pack(anchor="w", pady=(0, 8))
        tk.Button(appt_card, text="Abrir agenda →", font=self.f_small, fg=Theme.CYAN, bg=Theme.BG_PANEL,
                  bd=0, relief="flat", cursor="hand2",
                  command=lambda: self._log_activity("Agenda ainda não conectada", Theme.PURPLE)).pack(anchor="w")

        # -- memória --
        mem = tk.Frame(panel, bg=Theme.BG_PANEL_2, bd=1, relief="flat")
        mem.pack(fill="x", padx=14, pady=10)
        mem.configure(highlightbackground=Theme.BORDER, highlightthickness=1)
        row = tk.Frame(mem, bg=Theme.BG_PANEL_2)
        row.pack(fill="x", padx=10, pady=10)
        tk.Label(row, text="🧠", font=self.f_body, bg=Theme.BG_PANEL_2).pack(side="left", padx=(0, 8))
        col = tk.Frame(row, bg=Theme.BG_PANEL_2)
        col.pack(side="left")
        tk.Label(col, text="MEMÓRIA ATIVA", font=self.f_bold, fg=Theme.TEXT, bg=Theme.BG_PANEL_2).pack(anchor="w")
        tk.Label(col, text="Sistema de memória pronto", font=self.f_small, fg=Theme.TEXT_DIM,
                 bg=Theme.BG_PANEL_2).pack(anchor="w")
        tk.Label(row, text="●", font=self.f_body, fg=Theme.GREEN, bg=Theme.BG_PANEL_2).pack(side="right")

    def _panel_card(self, parent, title, dot_color=None, right_text=None):
        card = tk.Frame(parent, bg=Theme.BG_PANEL, bd=1, relief="flat")
        card.pack(fill="x", padx=14, pady=(14, 0))
        card.configure(highlightbackground=Theme.BORDER, highlightthickness=1)
        inner = tk.Frame(card, bg=Theme.BG_PANEL)
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        head = tk.Frame(inner, bg=Theme.BG_PANEL)
        head.pack(fill="x")
        tk.Label(head, text=title, font=self.f_small, fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL).pack(side="left")
        if right_text:
            tk.Label(head, text=right_text, font=self.f_small, fg=Theme.CYAN, bg=Theme.BG_PANEL).pack(side="right")
        elif dot_color:
            tk.Label(head, text="●", font=self.f_small, fg=dot_color, bg=Theme.BG_PANEL).pack(side="right")
        return inner

    def _system_row(self, parent, label, color):
        row = tk.Frame(parent, bg=Theme.BG_PANEL)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, font=self.f_small, fg=Theme.TEXT_DIM, bg=Theme.BG_PANEL,
                 width=5, anchor="w").pack(side="left")
        bar_bg = tk.Frame(row, bg=Theme.BORDER, height=6)
        bar_bg.pack(side="left", fill="x", expand=True, padx=8)
        bar = tk.Frame(bar_bg, bg=color, height=6, width=0)
        bar.place(x=0, y=0, relheight=1)
        val = tk.Label(row, text="—", font=self.f_small, fg=Theme.TEXT, bg=Theme.BG_PANEL, width=4)
        val.pack(side="right")
        return (bar, bar_bg), val

    # ==========================================
    # ESTADO DO NÚCLEO
    # ==========================================
    def _set_state(self, state):
        self.state_name = state
        label, desc, color = STATES.get(state, STATES["ready"])
        self.state_label.configure(text=label, fg=color)
        self.desc_label.configure(text=desc)
        self.orb.set_color(color)

    # ==========================================
    # CHAT
    # ==========================================
    def _set_placeholder(self):
        self.entry.delete(0, "end")

    def _add_message(self, text, kind="assistant"):
        self.chat_text.configure(state="normal")
        name = "VOCÊ" if kind == "user" else "JARVIS"
        tag = "name_user" if kind == "user" else "name_assistant"
        self.chat_text.insert("end", f"{name}\n", tag)
        self.chat_text.insert("end", f"{text}\n\n", "body")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def _clear_chat(self):
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.configure(state="disabled")
        self._add_message("Conversa limpa. Núcleo pronto.", "assistant")
        self._log_activity("Histórico visual limpo", Theme.PURPLE)

    def _send_command(self):
        command = self.entry.get().strip()
        if not command:
            return
        self._add_message(command, "user")
        self.entry.delete(0, "end")
        self._log_activity("Novo comando recebido", Theme.CYAN)
        self._set_state("thinking")
        self.send_btn.configure(state="disabled")
        self.mic_btn.configure(state="disabled")

        # processa "fora da thread da UI" pra simular latência sem travar a janela
        threading.Thread(target=self._process_and_reply, args=(command,), daemon=True).start()

    def _process_and_reply(self, command):
        time.sleep(random.uniform(0.4, 0.9))  # simula processamento
        try:
            reply, action = process_command(command)
            state = "executing" if action in ("programa", "abrir", "clicar") else "speaking"
            self.after(0, self._finish_command, reply, state, None)
        except Exception as exc:  # nunca deixa o núcleo travar em 'attention' silenciosamente
            self.after(0, self._finish_command, f"Não consegui concluir: {exc}", "attention", str(exc))

    def _finish_command(self, reply, state, error):
        self._set_state(state)
        self._add_message(reply, "assistant")
        if error:
            self._log_activity("Falha de comunicação", Theme.RED)
        else:
            self._log_activity("Resposta processada pelo núcleo", Theme.GREEN)
        self.send_btn.configure(state="normal")
        self.mic_btn.configure(state="normal")
        self.after(900, lambda: self._set_state("ready"))

    # ---------- modos / atalhos ----------
    def _mode_chat(self):
        self.mode_chat_btn.configure(bg=Theme.CYAN, fg=Theme.BG)
        self.mode_voice_btn.configure(bg=Theme.BG_PANEL_2, fg=Theme.TEXT_DIM)
        self._set_state("ready")
        self._log_activity("Modo Chat ativado", Theme.CYAN)
        self.entry.focus_set()

    def _mode_voice(self):
        self.mode_voice_btn.configure(bg=Theme.CYAN, fg=Theme.BG)
        self.mode_chat_btn.configure(bg=Theme.BG_PANEL_2, fg=Theme.TEXT_DIM)
        self._set_state("listening")
        self._log_activity("Modo Voz selecionado", Theme.GREEN)

    def _mic_click(self):
        self._mode_voice()
        self._log_activity("Microfone preparado", Theme.GREEN)
        self._add_message(
            "O módulo de reconhecimento de voz ainda não está conectado a esta interface. "
            "Assim que o Alfred tiver o pipeline de voz pronto, esse botão liga o microfone de verdade.",
            "assistant"
        )

    def _quick_voice(self):
        self._mic_click()

    def _quick_execute(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, "abrir calculadora")
        self._log_activity("Comando rápido preparado", Theme.CYAN)
        self.entry.focus_set()

    def _quick_memory(self):
        self._log_activity("Memória selecionada", Theme.PURPLE)
        self._add_message("O painel de memória está reservado para a integração do sistema de memória do Alfred.",
                           "assistant")

    # ==========================================
    # ATIVIDADE (feed lateral)
    # ==========================================
    def _log_activity(self, text, color):
        now = datetime.now().strftime("%H:%M:%S")
        self.activity_items.insert(0, (text, color, now))
        self.activity_items = self.activity_items[:7]
        self._render_activity()

    def _render_activity(self):
        for w in self.activity_frame.winfo_children():
            w.destroy()
        for text, color, when in self.activity_items:
            row = tk.Frame(self.activity_frame, bg=Theme.BG_PANEL)
            row.pack(fill="x", pady=3)
            tk.Label(row, text="●", font=self.f_small, fg=color, bg=Theme.BG_PANEL).pack(side="left", padx=(0, 6))
            col = tk.Frame(row, bg=Theme.BG_PANEL)
            col.pack(side="left")
            tk.Label(col, text=text, font=self.f_small, fg=Theme.TEXT, bg=Theme.BG_PANEL,
                     anchor="w", justify="left", wraplength=190).pack(anchor="w")
            tk.Label(col, text=when, font=self.f_small, fg=Theme.TEXT_FAINT, bg=Theme.BG_PANEL).pack(anchor="w")

    # ==========================================
    # RELÓGIO / SISTEMA
    # ==========================================
    def _update_clock(self):
        self.clock_label.configure(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._update_clock)

    def _update_system(self):
        if HAS_PSUTIL:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
        else:
            # sem psutil instalado: simula uma leitura plausível
            cpu = max(3, min(97, getattr(self, "_last_cpu", 20) + random.uniform(-6, 6)))
            ram = max(3, min(97, getattr(self, "_last_ram", 40) + random.uniform(-3, 3)))
            self._last_cpu, self._last_ram = cpu, ram

        self._set_bar(self.cpu_bar, cpu)
        self._set_bar(self.ram_bar, ram)
        self.cpu_val.configure(text=f"{int(cpu)}%")
        self.ram_val.configure(text=f"{int(ram)}%")
        self.after(2000, self._update_system)

    @staticmethod
    def _set_bar(bar_tuple, percent):
        bar, bar_bg = bar_tuple
        bar_bg.update_idletasks()
        width = bar_bg.winfo_width() or 140
        bar.place_configure(relwidth=max(0.02, min(1.0, percent / 100)))


# ==========================================
# INTÉRPRETE DE COMANDOS (placeholder do "cérebro")
# ==========================================

def process_command(command: str):
    """Interpreta um comando local simples e devolve (resposta, tipo_de_acao).

    Isso é só o ponto de entrada — a ideia é que, conforme o Alfred evolui
    (controle de pastas/abas, mouse/teclado, leitura de tela), essa função
    passe a delegar para os módulos reais em vez de responder na mão.
    """
    text = command.lower().strip()

    if any(p in text for p in ("que horas", "horas são", "hora atual")):
        return f"Agora são {datetime.now().strftime('%H:%M')}.", "consulta"

    if any(p in text for p in ("que dia", "data de hoje", "data atual")):
        return f"Hoje é {datetime.now().strftime('%d/%m/%Y')}.", "consulta"

    if "calculadora" in text:
        ok = _open_app("calc" if os.name == "nt" else "gnome-calculator")
        if ok:
            return "Abrindo a calculadora.", "abrir"
        return "Não consegui abrir a calculadora neste sistema.", "attention"

    if "bloco de notas" in text or "notepad" in text:
        ok = _open_app("notepad" if os.name == "nt" else "gedit")
        if ok:
            return "Abrindo o bloco de notas.", "abrir"
        return "Não consegui abrir o bloco de notas neste sistema.", "attention"

    if "navegador" in text or "internet" in text:
        ok = _open_app("start microsoft-edge:" if os.name == "nt" else "xdg-open http://")
        return ("Abrindo o navegador." if ok else "Não consegui abrir o navegador."), ("abrir" if ok else "attention")

    if text.startswith(("abra ", "abrir ")):
        alvo = text.split(" ", 1)[1]
        return f"Ainda não sei abrir '{alvo}' — isso será conectado ao módulo de controle do Alfred.", "abrir"

    if any(p in text for p in ("obrigado", "valeu")):
        return "Disponha! Estou por aqui.", "consulta"

    return (
        "Comando recebido. O núcleo de decisão do Alfred ainda não está "
        "conectado a esta interface — por enquanto eu só reconheço um "
        "punhado de comandos locais (hora, data, abrir calculadora/bloco "
        "de notas/navegador).",
        "consulta",
    )


def _open_app(command: str) -> bool:
    try:
        if os.name == "nt":
            os.startfile(command)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(command.split())
        return True
    except Exception:
        return False


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()