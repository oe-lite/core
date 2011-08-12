def format_textblock(text, indent=2, width=78):
    """
    Format a text block.

    This function formats a block of text. The text is broken into
    tokens. (Whitespace is NOT preserved.) The tokens are reassembled
    at the specified level of indentation and line width.  A string is
    returned.

    Arguments:
        `text`   -- the string to be reformatted.
        `indent` -- the integer number of spaces to indent by.
        `width`  -- the maximum width of formatted text (including indent).
    """
    width = width - indent
    out = []
    stack = [word for word in text.replace("\n", " ").split(" ") if word]
    while stack:
        line = ""
        while stack:
            if len(line) + len(" " + stack[0]) > width: break
            if line: line += " "
            line += stack.pop(0)
        out.append(" "*indent + line)
    return "\n".join(out)


class NullStream:
    def write(self, text):
        pass

class TeeStream:
    def __init__(self, files):
        self.files = files
        return
    def write(self, text):
        for file in self.files:
            file.write(text)
        return

def shcmd(cmd, dir=None, quiet=False, success_returncode=0):

    if type(cmd) == type([]):
        cmdlist = cmd
        cmd = cmdlist[0]
        for arg in cmdlist[1:]:
            cmd = cmd + ' ' + arg

    if dir:
        pwd = os.getcwd()
        chdir(dir, quiet=True)

    if not quiet:
        if dir:
            print '%s> %s'%(dir, cmd)
        else:
            print '> %s'%(cmd)

    retval = None
    if quiet:
        process = subprocess.Popen(cmd, shell=True, stdin=sys.stdin,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        output = process.communicate()[0]
        if process.returncode == success_returncode:
            retval = output

    else:
        returncode = subprocess.call(cmd, shell=True, stdin=sys.stdin)
        if returncode == success_returncode:
            retval = True

    if dir:
        chdir(pwd, quiet=True)

    return retval
