image bg room = Solid("#102030", xysize=(320, 180))
image bg hall = Solid("#203040", xysize=(320, 180))
image alice neutral = Solid("#cc0000", xysize=(64, 64))
image alice happy = Solid("#00cc00", xysize=(64, 64))
image bob = Solid("#0000cc", xysize=(64, 64))

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

init python:
    def layer_state():
        sl = renpy.game.context().scene_lists.layers["master"]
        return [{"tag": d.tag, "name": list(d.name), "zorder": d.zorder} for d in sl]

label start:
    $ emit("layer_initial", state=layer_state())
    scene bg room
    $ emit("layer_after_scene", state=layer_state())
    show alice neutral
    show bob
    $ emit("layer_after_shows", state=layer_state())
    show alice happy
    $ emit("layer_after_replace", state=layer_state())
    hide alice
    $ emit("layer_after_hide", state=layer_state())
    scene bg hall
    $ emit("layer_after_clear", state=layer_state())
    show bob at truecenter zorder 5
    $ emit("layer_after_zorder", state=layer_state())
    "display checked"
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

testcase display_ops:
    $ arm()
    run Jump("start")
    advance until screen "say"
    screenshot "display_final_layer"
    $ shot("display_final_layer")
    $ emit("test_pause")
    advance
    $ disarm()
    exit
