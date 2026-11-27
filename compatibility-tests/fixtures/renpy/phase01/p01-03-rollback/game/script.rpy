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

default counter = 0

label start:
    "A"
    $ counter += 1
    "B"
    $ counter += 1
    $ emit("at_b", counter=counter, can_rollback=renpy.can_rollback())
    "C"
    $ emit("at_c", counter=counter, can_rollback=renpy.can_rollback())
    $ renpy.rollback(True)
    $ emit("after_rollback", counter=counter)
    "D"
    $ emit("done", counter=counter)
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

testcase rollback_restores:
    $ arm()
    run Jump("start")
    advance until eval (store.counter == 2)
    $ emit("test_at_b", counter=store.counter, can_rollback=renpy.can_rollback())
    advance
    $ emit("test_after_rollback", counter=store.counter)
    advance
    $ emit("test_done", counter=store.counter)
    $ disarm()
    exit
