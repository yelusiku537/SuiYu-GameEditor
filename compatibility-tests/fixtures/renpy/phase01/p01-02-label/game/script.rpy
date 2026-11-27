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
    jump first_label
    return

label first_label:
    "in first label"
    jump second_label
    return

label second_label:
    "in second label"
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

testcase label_entry:
    $ arm()
    run Jump("first_label")
    advance until screen "say"
    advance
    $ disarm()
    exit

testcase label_from_start:
    $ arm()
    run Jump("start")
    advance until screen "say"
    advance
    advance
    $ disarm()
    exit
