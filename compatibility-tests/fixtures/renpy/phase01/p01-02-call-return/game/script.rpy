screen say(who, what):
    window:
        vbox:
            if who:
                text who id "who"
            text what id "what"

screen choice(items):
    vbox:
        for i in items:
            textbutton i.caption action i.action

label start:
    "outer before"
    call sub_one
    "outer after"
    $ finish()
    return

label sub_one:
    "in sub one"
    call sub_two
    "back in sub one"
    return

label sub_two:
    "in sub two"
    return

label returns_immediately:
    call empty_sub
    "after empty call"
    $ finish()
    return

label empty_sub:
    return

testsuite global:
    setup:
        $ _test.timeout = 25.0
        $ _test.transition_timeout = 0.05
        $ _test.screenshot_directory = "shots"
        $ _test.overwrite_screenshots = True
    teardown:
        exit

testcase nested_call:
    $ arm()
    run Jump("start")
    advance until screen "say"
    advance
    advance
    advance
    advance
    $ disarm()
    exit

testcase call_empty:
    $ arm()
    run Jump("returns_immediately")
    advance until screen "say"
    advance
    $ disarm()
    exit
