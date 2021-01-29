# -*- coding: utf-8 -*-
from setuptools import setup

setup(  name             = "n4d client",
        version          = "1.0",
        author           = "Enrique Medina Gremaldos",
        author_email     = "quiqueiii@gmail.com",
        url              = "https://github.com/edupals/python3-n4d-client",
        package_dir      = {'n4d.client': '.'},
        packages         = ['n4d.client'],
        data_files       = [('/usr/bin/',['n4d-client'])]
     )


