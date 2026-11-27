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

default points = 0
default named = "unset"
default listed = []
default allow_mutation = False

label start:
    $ emit("default_initial", points=points, named=named, listed=list(listed))
    if allow_mutation:
        $ points = 5
        $ named = "changed"
        $ listed.append("x")
        $ emit("default_mutated", points=points, named=named, listed=list(listed))
        $ renpy.save("default_slot")
        $ points = 99
        $ named = "after-save"
        $ emit("default_after_save", points=points, named=named)
    "checkpoint line"
    $ finish()
    return

label mutation:
    $ emit("loaded_defaults", points=points, named=named, listed=list(listed))
    return

label after_load:
    $ emit("after_load_defaults", points=points, named=named, listed=list(listed))
    return

testsuite global:
    setup:
        $ _test.timeout = 25.0
        $ _test.transition_timeout = 0.05
        $ _test.screenshot_directory = "shots"
        $ _test.overwrite_screenshots = True
    teardown:
        exit

testcase default_lifecycle:
    $ arm()
    $ store.allow_mutation = True
    run Jump("start")
    advance until screen "say"
    $ emit("test_barrier", points=store.points)
    advance
    $ disarm()
    exit

testcase default_after_load:
    $ arm()
    run Jump("mutation")
    $ emit("test_loaded", points=store.points, named=store.named)
    $ disarm()
    exit
