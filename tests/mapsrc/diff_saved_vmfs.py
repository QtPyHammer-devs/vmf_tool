import difflib


differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)

# BLANK
fromfile = open("blank.vmf", "r")
tofile = open("test_save_blank.vmf", "r")
out = differ.make_file(fromlines=fromfile.readlines(),
                       tolines=tofile.readlines())
with open("blank_vmf_diff.html", "w") as f:
    f.write(out)

# TEST2
fromfile = open("test2.vmf", "r")
tofile = open("test_save_test2.vmf", "r")
out = differ.make_file(fromlines=fromfile.readlines(),
                       tolines=tofile.readlines())
with open("test2_vmf_diff.html", "w") as f:
    f.write(out)
