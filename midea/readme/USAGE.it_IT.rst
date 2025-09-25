Sono presenti 2 tabelle che illustrano le funzionalità di base di Odoo e il flusso di
lavoro della migrazione.

La prima tabella si chiama "Midea QCI (non aziendale)", basata sul modello
Odoo "midea.qci" ed è una tabella generica, non dipendente dall'azienda.

La seconda tabella si chiama "Midea con azienda", basata sul modello
Odoo "midea.table_wco". Questa tabella dipende dall'azienda.

Entrambe le tabelle, insieme, gestiscono tutti i tipi di campo di Odoo,
così pè possibile veder come i campi di Odoo vengono visualizzati
nell'interfaccia utente nelle diverse versioni e come sono codificati nel
codice sorgente Python.

Sono gestite le seguenti funzionalità di Odoo:

* Campo "Char"
* Campo "Text"
* Campo "Html"
* Campo magico active ("Boolean")
* Campo magico state ("Selction")
* Campo "Date"
* Campo "Datetime"
* Campo "Integer"
* Campo magico sequence ("Integer")
* Campo "Float"
* Campo "Monetary"
* Campo magico company_id ("Many2one")
* Campo "One2many"
* Campo "Many2many"
* Campo "Binary"
* Campo magico immage ("Immage")
* Pulsanti per gestire il flusso di lavoro dello stato con la corretta visibilità
* Gestione campi invisibile e di sola lettura in base allo stato

Il codice sorgente originale è stato scritto su Odoo 12.0; tutte le altre versioni
vengono migrate automaticamente da arcangelo senza attività di sviluppo umano.
