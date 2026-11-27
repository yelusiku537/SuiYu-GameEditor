## Save / load fixture.
##
## Both testcases share one --savedir so the save and the load happen in
## separate processes:
##   save_case: play the save path and mutate past the checkpoint.
##   load_case: from loader_main, renpy.load("slot_a"); the engine runs
##              after_load in a fresh context, then resumes the saved flow.
##
## `start` never auto-loads. Only loader_main calls renpy.load, so each case is
## a single deterministic flow regardless of whether slot_a already exists.

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
default stage = "init"
default resumed = False

label start:
    "checkpoint line"
    $ points = 3
    $ stage = "pre-save"
    $ renpy.save("slot_a")
    $ emit("save_done", can_load=renpy.can_load("slot_a"), points=points, stage=stage)
    "after save line"
    $ points = 99
    $ stage = "mutated"
    $ emit("post_save_mutation", points=points, stage=stage)
    "finish line"
    $ finish()
    return

label after_load:
    ## Runs in the fresh load context before the saved flow resumes, so it
    ## observes the *initial* defaults rather than the saved values.
    $ emit("after_load_hook", points=points, stage=stage)
    $ resumed = True
    return

label loader_main:
    $ emit("loader_before", points=points, stage=stage)
    $ renpy.load("slot_a")
    $ emit("loader_after", note="unreachable on success")
    return

testsuite global:
    setup:
        $ _test.timeout = 25.0
        $ _test.transition_timeout = 0.05
        $ _test.screenshot_directory = "shots"
        $ _test.overwrite_screenshots = True
    teardown:
        exit

testcase save_case:
    $ arm()
    run Jump("start")
    advance until eval (store.stage == "mutated")
    exit

testcase load_case:
    $ arm()
    run Jump("loader_main")
    advance until eval store.resumed
    exit