
=========================================
|icon| Manage Test Environment 12.0.0.6.8
=========================================


**Create or update test environment**

.. |icon| image:: https://raw.githubusercontent.com/zeroincombenze/zerobug-test/12.0/mk_test_env/static/description/icon.png

|Maturity| |Build Status| |Codecov Status| |license gpl| |Try Me|


.. contents::



Overview / Panoramica
=====================

|en| Manage test environment
----------------------------

This module creates an test environment with test data.

The behaviour of this module, depends heavily from following PYPI modules:

* z0bug_odoo>=1.0.5.6: contains records data
* clodoo>=0.3.53.1: contains the odoo version depending translation
* odoo_score==1.0.3: odoo supercore


|

|it| Creazione ambiente di test
-------------------------------

Questo modulo crea un ambiente di test con dati di test.
Il comportamento di quesot modulo dipende pesantemente dai sequenti package PYPI:

* z0bug_odoo: contiene i dati dei record
* clodoo: contains le traduzioni dipendenti dalla versione di Odoo
* odoo_score: odoo supercore


|

Features / Caratteristiche
--------------------------

+------------------------------------------+------------+------------+------------+------------+---------+------------+---------+
| Description / Descrizione                | 6.1        | 7.0        | 8.0        | 9.0        | 10.0    | 11.0       | 12.0    |
+------------------------------------------+------------+------------+------------+------------+---------+------------+---------+
| Partner & Products / Soggetti e prodotti | |check|    | |check|    | |check|    | |check|    | |check| | |check|    | |check| |
+------------------------------------------+------------+------------+------------+------------+---------+------------+---------+
| Sale orders / Ordini clienti             | |no_check| | |no_check| | |no_check| | |no_check| | |check| | |no_check| | |check| |
+------------------------------------------+------------+------------+------------+------------+---------+------------+---------+
| Purchase orders / Ordini fornitori       | |no_check| | |no_check| | |no_check| | |no_check| | |check| | |no_check| | |check| |
+------------------------------------------+------------+------------+------------+------------+---------+------------+---------+
| Invoices / Fatture                       | |no_check| | |no_check| | |no_check| | |no_check| | |check| | |no_check| | |check| |
+------------------------------------------+------------+------------+------------+------------+---------+------------+---------+


|
|

Getting started / Come iniziare
===============================

|Try Me|


|

Installation / Installazione
----------------------------


+---------------------------------+------------------------------------------+
| |en|                            | |it|                                     |
+---------------------------------+------------------------------------------+
| These instructions are just an  | Istruzioni di esempio valide solo per    |
| example; use on Linux CentOS 7+ | distribuzioni Linux CentOS 7+,           |
| Ubuntu 14+ and Debian 8+        | Ubuntu 14+ e Debian 8+                   |
|                                 |                                          |
| Installation is built with:     | L'installazione è costruita con:         |
+---------------------------------+------------------------------------------+
| `Zeroincombenze Tools <https://zeroincombenze-tools.readthedocs.io/>`__    |
+---------------------------------+------------------------------------------+
| Suggested deployment is:        | Posizione suggerita per l'installazione: |
+---------------------------------+------------------------------------------+
| $HOME/12.0                                                                 |
+----------------------------------------------------------------------------+

::

    cd $HOME
    # *** Tools installation & activation ***
    # Case 1: you have not installed zeroincombenze tools
    git clone https://github.com/zeroincombenze/tools.git
    cd $HOME/tools
    ./install_tools.sh -p
    source $HOME/devel/activate_tools
    # Case 2: you have already installed zeroincombenze tools
    cd $HOME/tools
    ./install_tools.sh -U
    source $HOME/devel/activate_tools
    # *** End of tools installation or upgrade ***
    # Odoo repository installation; OCB repository must be installed
    odoo_install_repository zerobug-test -b 12.0 -O zero -o $HOME/12.0
    vem create $HOME/12.0/venv_odoo -O 12.0 -a "*" -DI -o $HOME/12.0

From UI: go to:

* |menu| Setting > Activate Developer mode 
* |menu| Apps > Update Apps List
* |menu| Setting > Apps |right_do| Select **mk_test_env** > Install


|

Upgrade / Aggiornamento
-----------------------


::

    cd $HOME
    # *** Tools installation & activation ***
    # Case 1: you have not installed zeroincombenze tools
    git clone https://github.com/zeroincombenze/tools.git
    cd $HOME/tools
    ./install_tools.sh -p
    source $HOME/devel/activate_tools
    # Case 2: you have already installed zeroincombenze tools
    cd $HOME/tools
    ./install_tools.sh -U
    source $HOME/devel/activate_tools
    # *** End of tools installation or upgrade ***
    # Odoo repository upgrade
    odoo_install_repository zerobug-test -b 12.0 -o $HOME/12.0 -U
    vem amend $HOME/12.0/venv_odoo -o $HOME/12.0
    # Adjust following statements as per your system
    sudo systemctl restart odoo

From UI: go to:

|

Support / Supporto
------------------


|Zeroincombenze| This module is maintained by the `SHS-AV s.r.l. <https://www.zeroincombenze.it/>`__


|
|

Get involved / Ci mettiamo in gioco
===================================

Bug reports are welcome! You can use the issue tracker to report bugs,
and/or submit pull requests on `GitHub Issues
<https://github.com/zeroincombenze/zerobug-test/issues>`_.

In case of trouble, please check there if your issue has already been reported.

Proposals for enhancement
-------------------------


|en| If you have a proposal to change this module, you may want to send an email to <cc@shs-av.com> for initial feedback.
An Enhancement Proposal may be submitted if your idea gains ground.

|it| Se hai proposte per migliorare questo modulo, puoi inviare una mail a <cc@shs-av.com> per un iniziale contatto.


ChangeLog History / Cronologia modifiche
----------------------------------------

12.0.0.6.8 (2021-11-16)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] mk_test_env: inventory data
* [IMP] mk_test_env: multiple journals

12.0.0.6.7 (2021-11-12)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] mk_test_env: conditioned import
* [IMP] mk_test_env: virtual xref for journal

12.0.0.6.6 (2021-11-11)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] mk_test_env: sometime does not load pyament modes

12.0.0.6.5 (2021-11-10)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] mk_test_env: data for test MtO
* [FIX] mk_test_env: minor fixes

12.0.0.6.4 (2021-11-09)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] mk_test_env: available for Odoo 10.0
* [IMP] mk_test_env: clean-up removed
* [IMP] mk_test_env: account wizard removed
* [FIX] mk_test_env: add does not change existing records

12.0.0.6.3 (2021-10-13)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] mk_test_env: default language and timezone from user
* [IMP] mk_test_env: new configuration for wallet management  / Nuova configurazione per conti di portafoglio

12.0.0.6.2 (2021-09-23)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] mk_test_env: added l10n_it_coa_base for distro powerp
* [FIX] mk_test_env: removed OCA supplemental SP modules for distro powerp

12.0.0.6.1 (2021-08-02)
~~~~~~~~~~~~~~~~~~~~~~~

* [IMP] Minor improvements

12.0.0.6 (2021-07-31)
~~~~~~~~~~~~~~~~~~~~~

* [REF] Refactoring



|
|

Credits / Didascalie
====================

Copyright
---------

Odoo is a trademark of `Odoo S.A. <https://www.odoo.com/>`__ (formerly OpenERP)



|

Authors / Autori
----------------

* `SHS-AV s.r.l. <https://www.zeroincombenze.it/>`__


Contributors / Collaboratori
----------------------------

* Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>


Maintainer / Manutenzione
-------------------------




|

----------------


|en| **zeroincombenze®** is a trademark of `SHS-AV s.r.l. <https://www.shs-av.com/>`__
which distributes and promotes ready-to-use **Odoo** on own cloud infrastructure.
`Zeroincombenze® distribution of Odoo <https://wiki.zeroincombenze.org/en/Odoo>`__
is mainly designed to cover Italian law and markeplace.

|it| **zeroincombenze®** è un marchio registrato da `SHS-AV s.r.l. <https://www.shs-av.com/>`__
che distribuisce e promuove **Odoo** pronto all'uso sulla propria infrastuttura.
La distribuzione `Zeroincombenze® <https://wiki.zeroincombenze.org/en/Odoo>`__ è progettata per le esigenze del mercato italiano.



|chat_with_us|


|

This module is part of zerobug-test project.

Last Update / Ultimo aggiornamento: 2021-11-18

.. |Maturity| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: 
.. |Build Status| image:: https://travis-ci.org/zeroincombenze/zerobug-test.svg?branch=12.0
    :target: https://travis-ci.com/zeroincombenze/zerobug-test
    :alt: github.com
.. |license gpl| image:: https://img.shields.io/badge/licence-LGPL--3-7379c3.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |license opl| image:: https://img.shields.io/badge/licence-OPL-7379c3.svg
    :target: https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html
    :alt: License: OPL
.. |Coverage Status| image:: https://coveralls.io/repos/github/zeroincombenze/zerobug-test/badge.svg?branch=12.0
    :target: https://coveralls.io/github/zeroincombenze/zerobug-test?branch=12.0
    :alt: Coverage
.. |Codecov Status| image:: https://codecov.io/gh/zeroincombenze/zerobug-test/branch/12.0/graph/badge.svg
    :target: https://codecov.io/gh/zeroincombenze/zerobug-test/branch/12.0
    :alt: Codecov
.. |Tech Doc| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-docs-12.svg
    :target: https://wiki.zeroincombenze.org/en/Odoo/12.0/dev
    :alt: Technical Documentation
.. |Help| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-help-12.svg
    :target: https://wiki.zeroincombenze.org/it/Odoo/12.0/man
    :alt: Technical Documentation
.. |Try Me| image:: https://www.zeroincombenze.it/wp-content/uploads/ci-ct/prd/button-try-it-12.svg
    :target: https://erp12.zeroincombenze.it
    :alt: Try Me
.. |OCA Codecov| image:: https://codecov.io/gh/OCA/zerobug-test/branch/12.0/graph/badge.svg
    :target: https://codecov.io/gh/OCA/zerobug-test/branch/12.0
    :alt: Codecov
.. |Odoo Italia Associazione| image:: https://www.odoo-italia.org/images/Immagini/Odoo%20Italia%20-%20126x56.png
   :target: https://odoo-italia.org
   :alt: Odoo Italia Associazione
.. |Zeroincombenze| image:: https://avatars0.githubusercontent.com/u/6972555?s=460&v=4
   :target: https://www.zeroincombenze.it/
   :alt: Zeroincombenze
.. |en| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/flags/en_US.png
   :target: https://www.facebook.com/Zeroincombenze-Software-gestionale-online-249494305219415/
.. |it| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/flags/it_IT.png
   :target: https://www.facebook.com/Zeroincombenze-Software-gestionale-online-249494305219415/
.. |check| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/check.png
.. |no_check| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/no_check.png
.. |menu| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/menu.png
.. |right_do| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/right_do.png
.. |exclamation| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/exclamation.png
.. |warning| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/warning.png
.. |same| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/same.png
.. |late| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/late.png
.. |halt| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/halt.png
.. |info| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/awesome/info.png
.. |xml_schema| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/certificates/iso/icons/xml-schema.png
   :target: https://github.com/zeroincombenze/grymb/blob/master/certificates/iso/scope/xml-schema.md
.. |DesktopTelematico| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/certificates/ade/icons/DesktopTelematico.png
   :target: https://github.com/zeroincombenze/grymb/blob/master/certificates/ade/scope/Desktoptelematico.md
.. |FatturaPA| image:: https://raw.githubusercontent.com/zeroincombenze/grymb/master/certificates/ade/icons/fatturapa.png
   :target: https://github.com/zeroincombenze/grymb/blob/master/certificates/ade/scope/fatturapa.md
.. |chat_with_us| image:: https://www.shs-av.com/wp-content/chat_with_us.gif
   :target: https://t.me/Assitenza_clienti_powERP

