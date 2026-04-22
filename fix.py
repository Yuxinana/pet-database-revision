with open("pawtrack_demo.html", "r") as f:
    content = f.read()

content = content.replace("'`<tr>", "`<tr>")
content = content.replace("</tr>`'", "</tr>`")

with open("pawtrack_demo.html", "w") as f:
    f.write(content)
