#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader


file_loader = FileSystemLoader('templates')
env = Environment(loader=file_loader)

template = env.get_template('template.tpl.yml')

output = template.render()
f = open("template.yml", "w+")
f.write(output)
f.close()
