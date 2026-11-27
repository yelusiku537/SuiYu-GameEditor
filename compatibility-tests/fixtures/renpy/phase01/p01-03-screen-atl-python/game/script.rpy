transform slide:
    xalign 0.0
    linear 0.1 xalign 1.0

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

screen hud():
    frame:
        text "HUD-VISIBLE" id "hudtext"

image eileen = Solid("#aa88ff", xysize=(64, 64))

label start:
    $ emit("screen_initial", shown=(renpy.get_screen("hud") is not None))
    show screen hud
    $ emit("screen_shown", shown=(renpy.get_screen("hud") is not None))
    show eileen at slide
    $ emit("atl_registered", in_at_list=bool(renpy.game.context().scene_lists.at_list.get("master", {}).get("eileen")))
    python:
        local_sum = sum(range(5))
        emit("embedded_python", local_sum=local_sum)
    hide screen hud
    $ emit("screen_hidden", shown=(renpy.get_screen("hud") is not None))
    "complex checked"
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

testcase screen_atl_python:
    $ arm()
    run Jump("start")
    advance until screen "say"
    advance
    $ disarm()
    exit
