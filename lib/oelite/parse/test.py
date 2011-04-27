#!/usr/bin/env python

conf_testmatrix = (

    ("hello = \"world\"\n",
     {'hello':{'':'world'}}),

    ("foo = 'bar'\n",
     {'foo':{'':'bar'}}),

    ("foo = 'bar'",
     {'foo':{'':'bar'}}),

    ("\nfoo = 'bar'",
     {'foo':{'':'bar'}}),

    ("foo = 'bar'\n\n",
     {'foo':{'':'bar'}}),

    ("export foo = 'bar'\n",
     {'foo':{'':'bar','export':'1'}}),

    ("export foo\n",
     {'foo':{'export':'1'}}),

    ("foo='bar'\nexport foo\n",
     {'foo':{'':'bar','export':'1'}}),

    ("export foo\nfoo='bar'\n",
     {'foo':{'':'bar','export':'1'}}),

    ("hello = \"world\"\nfoo = 'bar'\n",
     {'hello':{'':'world'}, 'foo':{'':'bar'}}),

    ("hello = \"world\"\nfoo = 'bar'\nint = 42\ntrue = True\nfalse = False\n",
     {'hello':{'':'world'},
      'foo':{'':'bar'},
      'int':{'':'42'},
      'true':{'':'1'},
      'false':{'':'0'}}),

    ("multiline = \"foo    \\\nbar \\\nhello world\"\n",
     {'multiline':{'':'foo    bar hello world'}}),


    (r"""foo = 'bar'
# en kommentar
  # endnu en kommentar
hello = 'world'""",
     {'foo':{'':'bar'}, 'hello':{'':'world'}}),

    ("test = 'foo'\ntest += 'bar'\n",
     {'test':{'':'foo bar'}}),

    ("test = 'foo'\ntest .= 'bar'\n",
     {'test':{'':'foobar'}}),

    ("test = 'foo'\ntest =+ 'bar'\n",
     {'test':{'':'bar foo'}}),

    ("test = 'foo'\ntest =. 'bar'\n",
     {'test':{'':'barfoo'}}),
     
    ("withspace = \"foo bar\"\n",
     {'withspace':{'':'foo bar'}}),

    ('quoteesc1 = "foo \\\"bar"\n',
     {'quoteesc1':{'':'foo "bar'}}),

    ("quoteesc1 = 'foo \\\'bar'\n",
     {'quoteesc1':{'':"foo 'bar"}}),

    ("hest[pony] = 'ko'\n",
     {'hest':{'pony':"ko"}}),

    ("include /tmp/foobar.inc\n",
     {'foo':{'':'bar'}}),

    ("include /tmp/foobar-no-such-thing.inc\n",
     {}),

    ("require /tmp/foobar.inc\n",
     {'foo':{'':'bar'}}),

    #("require /home/esben/oe-lite/master/conf/oe-lite.conf\n",
    # {'foo':{'':'bar'}}),

)

bb_testmatrix = (

    ("do_foobar () {\n  set -ex\n  echo hello world\n}\n",
     {'do_foobar':{'func':'sh','':'  set -ex\n  echo hello world\n'}}),

    ("fakeroot do_foobar () {\n  set -ex\n  echo hello world\n}\n",
     {'do_foobar':{'func':'sh','fakeroot':'1',
                   '':'  set -ex\n  echo hello world\n'}}),

    ("python do_foobar () {\n  import sys\n  print \"hello world\"\n}\n",
     {'do_foobar':{'func':'python',
                   '':'  import sys\n  print \"hello world\"\n'}}),
)

expand_testmatrix = (
    ('foo', 'foo'),
    ('${FOO}', 'bar'),
    ('xxx${FOO}', 'xxxbar'),
    ('${FOO}xxx', 'barxxx'),
    ('${FOO}${BAR}', 'barhello world'),
    ('${FOO}xxx${BAR}', 'barxxxhello world'),
    ('xxx${FOO}xxx', 'xxxbarxxx'),
    ('${F${oo}}', 'bar'),
    ('${${foo}}', 'bar'),
    ('${@["foo","bar"][0]}', 'foo'),
    ('${@["${FOO}","foo"][0]}', 'bar'),
    ('$ og {@ $ }', '$ og {@ $ }'),
)

if __name__ == "__main__":
    import confparse, bbparse, expandparse
    f = open("/tmp/foobar.inc", "w")
    f.write("foo='bar'\n")
    f.close()

    parser = confparse.ConfParser()
    passed = failed = 0
    for (testdata,expected_result) in conf_testmatrix:
        print "\n" + repr(testdata)
        parser.lextest(testdata, debug=True)
        result = parser.yacctest(testdata)
        if "dict" in dir(result):
            result = result.dict()
        if result != expected_result:
            print "result=%s\nexpected=%s\nFAIL"%(result, expected_result)
            failed += 1
        else:
            print "PASS"
            passed += 1
    print "\nPASSED = %d    FAILED = %d"%(passed, failed)

    parser = bbparse.BBParser()
    passed = failed = 0
    for (testdata,expected_result) in conf_testmatrix + bb_testmatrix:
        print "\n" + repr(testdata)
        parser.lextest(testdata, debug=True)
        result = parser.yacctest(testdata)
        if "dict" in dir(result):
            result = result.dict()
        if result != expected_result:
            print "result=%s\nexpected=%s\nFAIL"%(result, expected_result)
            failed += 1
        else:
            print "PASS"
            passed += 1
    print "\nPASSED = %d    FAILED = %d"%(passed, failed)

    data = parser.yacctest("FOO='bar'\nBAR='hello world'\nfoo='FOO'\noo='OO'")

    parser = expandparse.ExpandParser(data)
    passed = failed = 0
    for (testdata,expected_result) in expand_testmatrix:
        print "\n" + repr(testdata)
        parser.lextest(testdata, debug=True)
        result = parser.expand(testdata)
        if result != expected_result:
            print "result=%s\nexpected=%s\nFAIL"%(result, expected_result)
            failed += 1
        else:
            print "PASS"
            passed += 1
    print "\nPASSED = %d    FAILED = %d"%(passed, failed)

