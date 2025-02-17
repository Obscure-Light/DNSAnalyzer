#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modulo: dns_analyzer_app
------------------------
Applicazione Python con GUI per l'analisi dei record DNS di uno o più domini.
Consente di:
  - Aggiungere e rimuovere domini da una lista.
  - Importare domini e selettori DKIM da file di testo o CSV.
  - Selezionare i tipi di record DNS da analizzare (A, AAAA, MX, NS, CNAME, TXT, SPF, DMARC, DKIM, SOA, CAA).
  - Inserire e rimuovere selettori DKIM.
  - Avviare l’analisi e visualizzare i risultati in un’apposita area di testo.
  - Esportare i risultati in CSV, Excel (.xlsx) o JSON.
  - Abilitare una verifica "Best Practice" su alcuni record (SPF, DMARC, DKIM, MX, A/AAAA, NS).

Dipendenze:
  - Python 3.x
  - Tkinter (incluso di default con Python)
  - dnspython:   pip install dnspython
  - pandas:      pip install pandas
  - openpyxl:    pip install openpyxl

"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import dns.resolver
import pandas as pd


class DNSAnalyzerApp:
    """
    Classe principale che gestisce l'interfaccia grafica e l'analisi DNS.
    """
    def __init__(self, master):
        """
        Inizializza la finestra principale, il canvas con barre di scorrimento
        e i frame interni per domini, record DNS, selettori DKIM, risultati e pulsanti di azione.
        """
        self.master = master
        self.master.title("DNS Analyzer")
        self.master.geometry("800x600")

        # Canvas + scrollbar verticali/orizzontali
        self.canvas = tk.Canvas(self.master)
        self.canvas.pack(side='left', fill='both', expand=True)

        self.v_scrollbar = ttk.Scrollbar(self.master, orient='vertical', command=self.canvas.yview)
        self.v_scrollbar.pack(side='right', fill='y')

        self.h_scrollbar = ttk.Scrollbar(self.master, orient='horizontal', command=self.canvas.xview)
        self.h_scrollbar.pack(side='bottom', fill='x')

        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Frame contenitore inserito nel canvas
        self.container = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.container, anchor='nw')

        # Ricalcola l'area di scrolling quando il contenuto cambia dimensione
        self.container.bind("<Configure>", self.on_frame_configure)

        # Liste e variabili
        self.domains = []
        self.dkim_selectors = []
        self.record_types = ["A", "AAAA", "MX", "NS", "CNAME", "TXT", "SPF", "DMARC", "DKIM", "SOA", "CAA"]
        self.selected_record_types = {rt: tk.BooleanVar(value=False) for rt in self.record_types}

        # Variabile per abilitare l'analisi best practice
        self.enable_best_practices = tk.BooleanVar(value=False)

        # Creazione dei frame interni
        self.frame_domains = ttk.LabelFrame(self.container, text="Gestione Domini")
        self.frame_domains.pack(fill='x', padx=10, pady=5)

        self.frame_records = ttk.LabelFrame(self.container, text="Selezione Record DNS")
        self.frame_records.pack(fill='x', padx=10, pady=5)

        self.frame_dkim = ttk.LabelFrame(self.container, text="Gestione Selettori DKIM")
        self.frame_dkim.pack(fill='x', padx=10, pady=5)

        self.frame_results = ttk.LabelFrame(self.container, text="Risultati Analisi")
        self.frame_results.pack(fill='both', expand=True, padx=10, pady=5)

        self.frame_actions = ttk.Frame(self.container)
        self.frame_actions.pack(fill='x', padx=10, pady=5)

        # Richiamiamo le funzioni di creazione GUI
        self.create_domain_frame()
        self.create_records_frame()
        self.create_dkim_frame()
        self.create_results_frame()
        self.create_action_buttons()

        # Per salvare i risultati in memoria e poterli esportare successivamente
        self.analysis_results = pd.DataFrame()

    def on_frame_configure(self, event):
        """Aggiorna l'area scrollabile del canvas."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # --------------------- CREAZIONE DEI VARI PEZZI DI GUI ---------------------

    def create_domain_frame(self):
        """Frame per l'aggiunta/rimozione/import dei domini."""
        self.domain_entry = ttk.Entry(self.frame_domains, width=50)
        self.domain_entry.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        add_domain_btn = ttk.Button(self.frame_domains, text="Aggiungi Dominio", command=self.add_domain)
        add_domain_btn.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        import_domain_btn = ttk.Button(self.frame_domains, text="Importa da File", command=self.import_domains_from_file)
        import_domain_btn.grid(row=0, column=2, padx=5, pady=5, sticky='w')

        remove_domain_btn = ttk.Button(self.frame_domains, text="Rimuovi Dominio", command=self.remove_selected_domain)
        remove_domain_btn.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        # Lista domini
        self.domain_list = ttk.Treeview(self.frame_domains, columns=("Domain",), show="headings", height=5)
        self.domain_list.heading("Domain", text="Dominio")
        self.domain_list.column("Domain", width=300)
        self.domain_list.grid(row=1, column=0, columnspan=4, padx=5, pady=5)

        # Scrollbar verticale per la lista domini
        domain_scroll = ttk.Scrollbar(self.frame_domains, orient="vertical", command=self.domain_list.yview)
        self.domain_list.configure(yscroll=domain_scroll.set)
        domain_scroll.grid(row=1, column=4, sticky='ns', pady=5)

    def create_records_frame(self):
        """Frame con le checkbox per selezionare i vari record DNS."""
        record_checkboxes_frame = ttk.Frame(self.frame_records)
        record_checkboxes_frame.pack(fill='x', padx=5, pady=5)

        for i, rt in enumerate(self.record_types):
            cb = ttk.Checkbutton(record_checkboxes_frame, text=rt, variable=self.selected_record_types[rt])
            cb.grid(row=0, column=i, padx=2, pady=2)

        select_all_btn = ttk.Button(self.frame_records, text="Seleziona Tutto", command=self.select_all_records)
        select_all_btn.pack(anchor='e', padx=5, pady=5)

    def create_dkim_frame(self):
        """Frame per aggiunta/rimozione/import dei selettori DKIM."""
        self.dkim_entry = ttk.Entry(self.frame_dkim, width=30)
        self.dkim_entry.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        add_dkim_btn = ttk.Button(self.frame_dkim, text="Aggiungi Selettore", command=self.add_dkim_selector)
        add_dkim_btn.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        import_dkim_btn = ttk.Button(self.frame_dkim, text="Importa Selettori da File", command=self.import_dkim_from_file)
        import_dkim_btn.grid(row=0, column=2, padx=5, pady=5, sticky='w')

        remove_dkim_btn = ttk.Button(self.frame_dkim, text="Rimuovi Selettore", command=self.remove_selected_dkim)
        remove_dkim_btn.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        # Lista selettori DKIM
        self.dkim_list = ttk.Treeview(self.frame_dkim, columns=("Selector",), show="headings", height=5)
        self.dkim_list.heading("Selector", text="Selettore DKIM")
        self.dkim_list.column("Selector", width=200)
        self.dkim_list.grid(row=1, column=0, columnspan=4, padx=5, pady=5)

        # Scrollbar verticale per la lista DKIM
        dkim_scroll = ttk.Scrollbar(self.frame_dkim, orient="vertical", command=self.dkim_list.yview)
        self.dkim_list.configure(yscroll=dkim_scroll.set)
        dkim_scroll.grid(row=1, column=4, sticky='ns', pady=5)

    def create_results_frame(self):
        """Frame che mostra i risultati dell’analisi in una Textbox con scrollbar."""
        self.results_text = tk.Text(self.frame_results, wrap='word')
        self.results_text.pack(fill='both', expand=True, padx=5, pady=5)

        results_scroll = ttk.Scrollbar(self.frame_results, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscroll=results_scroll.set)
        results_scroll.pack(side='right', fill='y')

    def create_action_buttons(self):
        """Frame con i pulsanti per avviare l'analisi, esportare i risultati e abilitare best practice."""
        start_analysis_btn = ttk.Button(self.frame_actions, text="Avvia Analisi", command=self.run_analysis)
        start_analysis_btn.pack(side='left', padx=5, pady=5)

        export_results_btn = ttk.Button(self.frame_actions, text="Esporta Risultati", command=self.export_results)
        export_results_btn.pack(side='left', padx=5, pady=5)

        bp_checkbox = ttk.Checkbutton(
            self.frame_actions,
            text="Abilita Analisi Best Practice",
            variable=self.enable_best_practices
        )
        bp_checkbox.pack(side='left', padx=5, pady=5)

    # --------------------- FUNZIONI PER GESTIONE DOMINI ---------------------

    def add_domain(self):
        """Aggiunge un dominio alla lista, evitando duplicati e stringhe vuote."""
        domain = self.domain_entry.get().strip()
        if domain and domain not in self.domains:
            self.domains.append(domain)
            self.domain_list.insert("", "end", values=(domain,))
            self.domain_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Attenzione", "Il dominio è già presente o il campo è vuoto.")

    def import_domains_from_file(self):
        """Importa domini da file di testo o CSV, un dominio per riga."""
        file_path = filedialog.askopenfilename(
            title="Seleziona file",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        domain = line.strip()
                        if domain and domain not in self.domains:
                            self.domains.append(domain)
                            self.domain_list.insert("", "end", values=(domain,))
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile leggere il file: {e}")

    def remove_selected_domain(self):
        """Rimuove il dominio selezionato dalla lista."""
        selected_item = self.domain_list.selection()
        if selected_item:
            for item in selected_item:
                domain = self.domain_list.item(item)['values'][0]
                self.domains.remove(domain)
                self.domain_list.delete(item)
        else:
            messagebox.showwarning("Attenzione", "Seleziona un dominio dalla lista.")

    # --------------------- FUNZIONI PER GESTIONE RECORD ---------------------

    def select_all_records(self):
        """Seleziona tutti i record DNS possibili."""
        for rt in self.selected_record_types:
            self.selected_record_types[rt].set(True)

    # --------------------- FUNZIONI PER GESTIONE SELETTORI DKIM ---------------------

    def add_dkim_selector(self):
        """Aggiunge un selettore DKIM evitando duplicati e stringhe vuote."""
        selector = self.dkim_entry.get().strip()
        if selector and selector not in self.dkim_selectors:
            self.dkim_selectors.append(selector)
            self.dkim_list.insert("", "end", values=(selector,))
            self.dkim_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Attenzione", "Il selettore è già presente o il campo è vuoto.")

    def import_dkim_from_file(self):
        """Importa selettori DKIM da un file di testo o CSV, un selettore per riga."""
        file_path = filedialog.askopenfilename(
            title="Seleziona file",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        selector = line.strip()
                        if selector and selector not in self.dkim_selectors:
                            self.dkim_selectors.append(selector)
                            self.dkim_list.insert("", "end", values=(selector,))
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile leggere il file: {e}")

    def remove_selected_dkim(self):
        """Rimuove il selettore DKIM selezionato dalla lista."""
        selected_item = self.dkim_list.selection()
        if selected_item:
            for item in selected_item:
                selector = self.dkim_list.item(item)['values'][0]
                self.dkim_selectors.remove(selector)
                self.dkim_list.delete(item)
        else:
            messagebox.showwarning("Attenzione", "Seleziona un selettore dalla lista.")

    # ---------------------- FUNZIONI DI ANALISI E BEST PRACTICE ----------------------

    def severity_level(self, sev):
        """
        Mappa la stringa severity in un livello numerico per confronti:
          CRITICAL > WARN > INFO > OK
        """
        levels = {"CRITICAL": 4, "WARN": 3, "INFO": 2, "OK": 1, "": 0}
        return levels.get(sev, 0)

    def check_best_practices(self, record_type, record_value_list):
        """
        Verifica alcune best practice su determinati record DNS:
            SPF, DMARC, DKIM, MX, A/AAAA, NS.
        Ritorna una tupla (severity, details):
            severity: { "OK", "WARN", "CRITICAL", "INFO" }
            details: stringa descrittiva.
        """
        severity = "OK"
        issues = []

        combined_value = " | ".join(record_value_list).lower()

        # SPF
        if record_type == "SPF":
            count_includes = combined_value.count("include:")
            if count_includes > 10:
                severity = "WARN"
                issues.append(f"SPF con {count_includes} include (possibili troppe query DNS)")

            if "all" in combined_value:
                if "-all" not in combined_value and "~all" not in combined_value and "?all" not in combined_value:
                    # Non ha alcun suffisso -all, ~all, ?all
                    new_sev = "WARN"
                    severity = max(severity, new_sev, key=self.severity_level)
                    issues.append("SPF privo di suffisso standard (-all/~all/?all)")
                else:
                    if "~all" in combined_value:
                        new_sev = "WARN"
                        severity = max(severity, new_sev, key=self.severity_level)
                        issues.append("SPF con ~all (softfail)")
                    elif "?all" in combined_value:
                        new_sev = "WARN"
                        severity = max(severity, new_sev, key=self.severity_level)
                        issues.append("SPF con ?all (neutral)")

            for val in record_value_list:
                if len(val) > 255:
                    new_sev = "WARN"
                    severity = max(severity, new_sev, key=self.severity_level)
                    issues.append(f"Record SPF molto lungo ({len(val)} caratteri)")

            if "include:*" in combined_value:
                new_sev = "CRITICAL"
                severity = max(severity, new_sev, key=self.severity_level)
                issues.append("SPF usa include:* (wildcard) - configurazione rischiosa")

        # DMARC
        elif record_type == "DMARC":
            if "v=dmarc1" not in combined_value:
                severity = "CRITICAL"
                issues.append("DMARC non valido (manca v=DMARC1)")

            if "p=none" in combined_value:
                new_sev = "WARN"
                severity = max(severity, new_sev, key=self.severity_level)
                issues.append("DMARC policy = none (protezione debole)")

            if "rua=" not in combined_value and "ruf=" not in combined_value:
                if severity == "OK":
                    severity = "INFO"
                issues.append("Nessun indirizzo di report (rua/ruf) configurato")

            if len(record_value_list) > 1:
                new_sev = "CRITICAL"
                severity = max(severity, new_sev, key=self.severity_level)
                issues.append("DMARC duplicato: trovati più record v=DMARC1")

        # DKIM
        elif record_type == "DKIM":
            if "p=" not in combined_value:
                new_sev = "CRITICAL"
                severity = max(severity, new_sev, key=self.severity_level)
                issues.append("Chiave DKIM non valida (manca p=)")

            if "k=rsa" not in combined_value:
                new_sev = "WARN"
                severity = max(severity, new_sev, key=self.severity_level)
                issues.append("Record DKIM senza k=rsa (o non esplicitato)")

            for val in record_value_list:
                if "p=" in val:
                    splitted = val.split("p=")
                    if len(splitted) > 1:
                        key_part = splitted[1].split(";")[0].strip()
                        key_len = len(key_part)
                        if key_len < 160:
                            new_sev = "CRITICAL"
                            severity = max(severity, new_sev, key=self.severity_level)
                            issues.append("Chiave DKIM estremamente corta (<1024 bit?)")
                        elif key_len < 300:
                            new_sev = "WARN"
                            severity = max(severity, new_sev, key=self.severity_level)
                            issues.append("Chiave DKIM più corta di 2048 bit; sicurezza migliorabile.")

            if len(record_value_list) > 1:
                new_sev = "WARN"
                severity = max(severity, new_sev, key=self.severity_level)
                issues.append("Selettore DKIM definito più volte.")

        # MX
        elif record_type == "MX":
            if not record_value_list:
                new_sev = "CRITICAL"
                severity = max(severity, new_sev, key=self.severity_level)
                issues.append("Nessun record MX trovato.")

            # Controllo priorità (se tutti uguali, WARN)
            priorities = []
            for val in record_value_list:
                parts = val.split()
                if len(parts) == 2:
                    try:
                        pr = int(parts[0])
                        priorities.append(pr)
                    except:
                        pass
            if len(set(priorities)) == 1 and len(priorities) > 1:
                new_sev = "WARN"
                severity = max(severity, new_sev, key=self.severity_level)
                issues.append("Tutti i record MX hanno la stessa priorità (nessun fallback).")

        # A/AAAA
        elif record_type in ["A", "AAAA"]:
            import ipaddress
            for addr in record_value_list:
                try:
                    ip_obj = ipaddress.ip_address(addr)
                    if ip_obj.is_private:
                        new_sev = "WARN"
                        severity = max(severity, new_sev, key=self.severity_level)
                        issues.append(f"Indirizzo {addr} è privato (non raggiungibile da Internet?).")
                except:
                    pass

        # NS
        elif record_type == "NS":
            if len(record_value_list) < 2:
                new_sev = "WARN"
                severity = max(severity, new_sev, key=self.severity_level)
                issues.append("Solo un nameserver (best practice: almeno due).")

        return severity, "; ".join(issues)

    # --------------------- FUNZIONI PER L'ESECUZIONE DELL’ANALISI ---------------------

    def run_analysis(self):
        """
        Avvia l’analisi DNS sui domini e sui record selezionati.
        Stampa i risultati in self.results_text e li salva in self.analysis_results.
        """
        self.results_text.delete("1.0", tk.END)

        if not self.domains:
            self.results_text.insert(tk.END, "Nessun dominio da analizzare.\n")
            return

        selected_rtypes = [rt for rt, val in self.selected_record_types.items() if val.get()]

        # Se Best Practice è abilitato ma nessun record selezionato, analizziamo in automatico un set default
        if self.enable_best_practices.get() and not selected_rtypes:
            selected_rtypes = ["SPF", "DMARC", "DKIM", "MX", "A", "AAAA", "NS"]

        if not selected_rtypes:
            self.results_text.insert(tk.END, "Nessun tipo di record selezionato.\n")
            return

        resolver = dns.resolver.Resolver()
        results = []

        for domain in self.domains:
            for rtype in selected_rtypes:
                # Gestione DKIM
                if rtype == "DKIM":
                    if not self.dkim_selectors:
                        self.results_text.insert(tk.END, f"[{domain}] Nessun selettore DKIM fornito.\n")
                        continue
                    for selector in self.dkim_selectors:
                        dkim_domain = f"{selector}._domainkey.{domain}"
                        try:
                            answer = resolver.resolve(dkim_domain, "TXT")
                            records = [r.to_text() for r in answer]

                            if self.enable_best_practices.get():
                                severity, bp_details = self.check_best_practices("DKIM", records)
                            else:
                                severity, bp_details = ("", "")

                            results.append({
                                "Domain": domain,
                                "RecordType": "DKIM",
                                "Selector": selector,
                                "Value": "|".join(records),
                                "Issues": "",
                                "Severity": severity,
                                "BP_Details": bp_details
                            })
                            self.results_text.insert(tk.END, f"[{domain}] DKIM ({selector}): {records}\n")
                            if self.enable_best_practices.get() and severity and severity != "OK":
                                self.results_text.insert(tk.END, f"    => [SEVERITY: {severity}] {bp_details}\n")

                        except Exception as e:
                            results.append({
                                "Domain": domain,
                                "RecordType": "DKIM",
                                "Selector": selector,
                                "Value": str(e),
                                "Issues": "Errore risoluzione DKIM",
                                "Severity": "CRITICAL" if self.enable_best_practices.get() else "",
                                "BP_Details": "Errore di lookup" if self.enable_best_practices.get() else ""
                            })
                            self.results_text.insert(tk.END, f"[{domain}] DKIM ({selector}) ERRORE: {e}\n")

                # Gestione DMARC
                elif rtype == "DMARC":
                    dmarc_domain = f"_dmarc.{domain}"
                    try:
                        answer = resolver.resolve(dmarc_domain, "TXT")
                        records = [r.to_text() for r in answer]

                        if self.enable_best_practices.get():
                            severity, bp_details = self.check_best_practices("DMARC", records)
                        else:
                            severity, bp_details = ("", "")

                        dmarc_records = [rec for rec in records if "v=DMARC1" in rec]
                        if dmarc_records:
                            results.append({
                                "Domain": domain,
                                "RecordType": "DMARC",
                                "Selector": "",
                                "Value": "|".join(dmarc_records),
                                "Issues": "",
                                "Severity": severity,
                                "BP_Details": bp_details
                            })
                            self.results_text.insert(tk.END, f"[{domain}] DMARC: {dmarc_records}\n")
                            if self.enable_best_practices.get() and severity and severity != "OK":
                                self.results_text.insert(tk.END, f"    => [SEVERITY: {severity}] {bp_details}\n")
                        else:
                            # Non c'è un record v=DMARC1 valido
                            results.append({
                                "Domain": domain,
                                "RecordType": "DMARC",
                                "Selector": "",
                                "Value": "Nessun record DMARC valido",
                                "Issues": "Nessun record DMARC con v=DMARC1",
                                "Severity": "CRITICAL" if self.enable_best_practices.get() else "",
                                "BP_Details": "DMARC non valido" if self.enable_best_practices.get() else ""
                            })
                            self.results_text.insert(tk.END, f"[{domain}] DMARC ERRORE: nessun record v=DMARC1\n")
                    except Exception as e:
                        results.append({
                            "Domain": domain,
                            "RecordType": "DMARC",
                            "Selector": "",
                            "Value": str(e),
                            "Issues": "DMARC assente o non valido",
                            "Severity": "CRITICAL" if self.enable_best_practices.get() else "",
                            "BP_Details": "Errore di lookup" if self.enable_best_practices.get() else ""
                        })
                        self.results_text.insert(tk.END, f"[{domain}] DMARC ERRORE: {e}\n")

                # Gestione SPF
                elif rtype == "SPF":
                    try:
                        answer = resolver.resolve(domain, "TXT")
                        records = [r.to_text() for r in answer]
                        spf_records = [rec for rec in records if "v=spf1" in rec.lower()]

                        if spf_records:
                            if self.enable_best_practices.get():
                                severity, bp_details = self.check_best_practices("SPF", spf_records)
                            else:
                                severity, bp_details = ("", "")

                            results.append({
                                "Domain": domain,
                                "RecordType": "SPF",
                                "Selector": "",
                                "Value": "|".join(spf_records),
                                "Issues": "",
                                "Severity": severity,
                                "BP_Details": bp_details
                            })
                            self.results_text.insert(tk.END, f"[{domain}] SPF: {spf_records}\n")
                            if self.enable_best_practices.get() and severity and severity != "OK":
                                self.results_text.insert(tk.END, f"    => [SEVERITY: {severity}] {bp_details}\n")
                        else:
                            results.append({
                                "Domain": domain,
                                "RecordType": "SPF",
                                "Selector": "",
                                "Value": "Nessun record SPF trovato",
                                "Issues": "SPF assente o non valido",
                                "Severity": "CRITICAL" if self.enable_best_practices.get() else "",
                                "BP_Details": "Manca v=spf1" if self.enable_best_practices.get() else ""
                            })
                            self.results_text.insert(tk.END, f"[{domain}] SPF ERRORE: Nessun record SPF trovato\n")
                    except Exception as e:
                        results.append({
                            "Domain": domain,
                            "RecordType": "SPF",
                            "Selector": "",
                            "Value": str(e),
                            "Issues": "SPF assente o non valido",
                            "Severity": "CRITICAL" if self.enable_best_practices.get() else "",
                            "BP_Details": "Errore di lookup" if self.enable_best_practices.get() else ""
                        })
                        self.results_text.insert(tk.END, f"[{domain}] SPF ERRORE: {e}\n")

                # Gestione altri record
                else:
                    try:
                        answer = resolver.resolve(domain, rtype)
                        records = [r.to_text() for r in answer]

                        if self.enable_best_practices.get():
                            severity, bp_details = self.check_best_practices(rtype, records)
                        else:
                            severity, bp_details = ("", "")

                        results.append({
                            "Domain": domain,
                            "RecordType": rtype,
                            "Selector": "",
                            "Value": "|".join(records),
                            "Issues": "",
                            "Severity": severity,
                            "BP_Details": bp_details
                        })
                        self.results_text.insert(tk.END, f"[{domain}] {rtype}: {records}\n")
                        if self.enable_best_practices.get() and severity and severity != "OK":
                            self.results_text.insert(tk.END, f"    => [SEVERITY: {severity}] {bp_details}\n")

                    except Exception as e:
                        results.append({
                            "Domain": domain,
                            "RecordType": rtype,
                            "Selector": "",
                            "Value": str(e),
                            "Issues": f"Errore risoluzione {rtype}",
                            "Severity": "CRITICAL" if self.enable_best_practices.get() else "",
                            "BP_Details": "Errore di lookup" if self.enable_best_practices.get() else ""
                        })
                        self.results_text.insert(tk.END, f"[{domain}] {rtype} ERRORE: {e}\n")

        # Convertiamo in DataFrame per l'esportazione
        self.analysis_results = pd.DataFrame(
            results,
            columns=["Domain", "RecordType", "Selector", "Value", "Issues", "Severity", "BP_Details"]
        )

    # --------------------- FUNZIONI PER L'ESPORTAZIONE DEI RISULTATI ---------------------

    def export_results(self):
        """Permette di scegliere il formato (CSV, XLSX, JSON) e salva i risultati."""
        if self.analysis_results.empty:
            messagebox.showwarning("Attenzione", "Non ci sono risultati da esportare.")
            return

        export_window = tk.Toplevel(self.master)
        export_window.title("Esporta Risultati")
        export_window.geometry("300x150")

        ttk.Label(export_window, text="Scegli il formato di esportazione:").pack(pady=10)

        def do_export(fmt):
            export_window.destroy()
            self.save_results(fmt)

        ttk.Button(export_window, text="CSV", command=lambda: do_export("csv")).pack(pady=5)
        ttk.Button(export_window, text="Excel (.xlsx)", command=lambda: do_export("xlsx")).pack(pady=5)
        ttk.Button(export_window, text="JSON", command=lambda: do_export("json")).pack(pady=5)

    def save_results(self, fmt):
        """Salva fisicamente su disco il DataFrame dei risultati."""
        filetypes = []
        if fmt == "csv":
            filetypes = [("CSV files", "*.csv")]
        elif fmt == "xlsx":
            filetypes = [("Excel files", "*.xlsx")]
        elif fmt == "json":
            filetypes = [("JSON files", "*.json")]

        filepath = filedialog.asksaveasfilename(defaultextension=f".{fmt}", filetypes=filetypes)
        if not filepath:
            return

        try:
            if fmt == "csv":
                self.analysis_results.to_csv(filepath, index=False)
            elif fmt == "xlsx":
                self.analysis_results.to_excel(filepath, index=False)
            elif fmt == "json":
                self.analysis_results.to_json(filepath, orient="records")

            messagebox.showinfo("Successo", f"Risultati esportati con successo in {filepath}")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile esportare i risultati: {e}")
