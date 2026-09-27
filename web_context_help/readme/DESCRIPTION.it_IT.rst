Aggiunge un pulsante |sos| al pannello di controllo di ogni vista: apre l'aiuto
della vista corrente in una finestra separata, così la scheda di Odoo resta
utilizzabile.

* Le pagine di aiuto sono scritte in RST da ogni modulo, nella cartella ``help/``
* La finestra di aiuto segue la navigazione (*Segui Odoo*), evidenzia i campi
  citati dalla pagina e può avviare un tour guidato
* Le domande hanno risposta da una ricerca testuale nelle sezioni di aiuto;
  ogni domanda è registrata per l'amministratore
* Gli amministratori possono modificare una pagina; la versione modificata
  sopravvive agli aggiornamenti e un avviso compare quando cambia la sorgente
* Le viste senza pagina ricevono una pagina automatica costruita dall'aiuto dei campi

.. |sos| unicode:: U+1F6DF
