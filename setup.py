# -*- coding: utf-8 -*-
from distutils.core import setup
from distutils.extension import Extension
import os
import subprocess

setup(  name             = "n4d client",
        version          = "1.0",
        author           = "Enrique Medina Gremaldos",
        author_email     = "quiqueiii@gmail.com",
        url              = "https://github.com/edupals/python3-n4d-client",
        package_dir      = {'': '.'},
        packages         = ['n4d']
     )


