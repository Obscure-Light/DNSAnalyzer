#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo: main
------------
Avvia l'applicazione DNSAnalyzerApp.
"""

import tkinter as tk
from dns_analyzer_app import DNSAnalyzerApp

def main():
    root = tk.Tk()
    app = DNSAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
