This module has no specific function for End-user,
it is designed for Odoo developers.

This module aims to:

* It shows the differences among different Odoo versions
* It is used to validate the z0bug_odoo package
* Define the qci table to manage test environment


Developer info
--------------

There are two table in this module: qci is independent from company,
the other is company dependent.
Here some difference among versions:

.. $include description_characters.csv


Test info
---------

The tests/test_midea file executes following unit tests:

* Import z0bug_odoo package -> validate the python package
* test_common.SingleTransactionCase -> validate test class
* create_id() function -> test result
* browse_rec() function -> excpected result
* write_rec() function -> test result by browsing again

*Notice test source code is quite identical across Odoo versions*.
