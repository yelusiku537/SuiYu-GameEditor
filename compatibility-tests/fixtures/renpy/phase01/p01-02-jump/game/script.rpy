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
    "before jump"
    jump destination
    return

label destination:
    "at destination"
    $ finish()
    return

label skip_middle:
    jump final_label
    return

label final_label:
    "at final label"
    $ finish()
    return

testsuite global:
    setup:
        $ _test.timeout = 25.0
        $ _test.transition_timeout = 0.05
        $ _test.screenshot_directory = "shots"
        $ _test.overwrite_screenshots = True
    teardown:
        exit

testcase jump_forward:
    $ arm()
    run Jump("start")
    advance until screen "say"
    advance
    advance
    $ disarm()
    exit

testcase jump_skip:
    $ arm()
    run Jump("skip_middle")
    advance until screen "say"
    advance
    $ disarm()
    exit
