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

define greeting = "hello"
define config_value = 42
define computed = 6 * 7
define char = Character("DefinedChar")

label start:
    $ emit("define_values",
           greeting=greeting,
           config_value=config_value,
           computed=computed,
           char_name=char.name)
    "define checked"
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

testcase define_init:
    $ arm()
    run Jump("start")
    advance until screen "say"
    advance
    $ disarm()
    exit
