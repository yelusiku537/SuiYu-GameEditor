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

define e = Character("Eileen")
default name_var = "Variable Name"

label start:
    "plain narration"
    e "character line"
    "line with quoted text"
    narrator "narrator explicit"
    e "substitution [name_var]"
    "two words"
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

testcase say_forms:
    $ arm()
    run Jump("start")
    advance until screen "say"
    screenshot "say_plain_narration"
    $ shot("say_plain_narration")
    advance
    advance
    advance
    advance
    advance
    advance
    $ disarm()
    exit
