image bg room = Solid("#102030", xysize=(320, 180))
image bg hall = Solid("#203040", xysize=(320, 180))

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
    scene bg room
    $ emit("transition_before", marker="room_shown")
    with dissolve
    $ emit("transition_after_dissolve", marker="dissolved_in")
    scene bg hall with fade
    $ emit("transition_after_fade", marker="hall_faded")
    "transition checked"
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

testcase transitions_apply:
    $ arm()
    run Jump("start")
    advance until screen "say"
    screenshot "transition_final"
    $ shot("transition_final")
    advance
    $ disarm()
    exit
