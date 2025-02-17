# DNS Analyzer GUI

Applicazione Python con interfaccia grafica (GUI) per l'analisi di record DNS su uno o più domini. Include funzionalità di verifica "best practice" per alcuni record sensibili (SPF, DMARC, DKIM, MX, A/AAAA, NS).

## Funzionalità Principali

1. **Gestione Domini**  
   - Aggiungi manualmente un dominio.  
   - Rimuovi un dominio selezionato.  
   - Importa domini da file `.txt` o `.csv` (un dominio per riga).

2. **Selezione Record DNS**  
   - Puoi selezionare quali record vuoi analizzare: A, AAAA, MX, NS, CNAME, TXT, SPF, DMARC, DKIM, SOA, CAA.  
   - Pulsante "Seleziona Tutto" per spuntare rapidamente tutti i record.

3. **Gestione Selettori DKIM**  
   - Aggiungi uno o più selettori DKIM manualmente.
   - Rimuovi un selettore selezionato.
   - Importa selettori da file `.txt` o `.csv`.

4. **Avvio Analisi**  
   - L’applicazione esegue query DNS per tutti i domini presenti in lista e per i record selezionati.  
   - Visualizza i risultati in una finestra di testo.

5. **Analisi Best Practice** (Opzionale)  
   - Abilita la checkbox “Abilita Analisi Best Practice” per controllare potenziali problemi noti su SPF, DMARC, DKIM, MX, A/AAAA, NS.  
   - Vengono aggiunte colonne di severità (`Severity`) e dettagli specifici (`BP_Details`) nelle esportazioni.  
   - Se non selezioni alcun record ma abiliti questa analisi, verranno comunque controllati di default SPF, DMARC, DKIM, MX, A, AAAA e NS.

6. **Esportazione Risultati**  
   - Puoi esportare i risultati in formato `.csv`, `.xlsx` (Excel) o `.json`.

## Requisiti

- **Python 3.x**
- **Tkinter** (incluso di default in molte distribuzioni Python, se non presente può essere necessario installarlo separatamente su alcune piattaforme)
- **dnspython** per le query DNS  
  ```bash
  pip install dnspython
