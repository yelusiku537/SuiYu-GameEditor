## Startup chain fixture.
##
## Proves that a project reaches `label start` and that init-time definitions
## are visible there. The earlier boot/compile stages happen before any script
## runs, so they cannot be observed from inside the game; they are evidenced
## separately by the check script through `compile` artifacts and
## `run --json-dump` label/source maps (see docs/compatibility/startup-chain.md).

screen say(who, what):
    window:
        vbox:
            if who:
                text who id "who"
            text what id "what"

## Definitions created at different init priorities. If a later init block ran
## first, these values would be wrong when `start` executes.
define startup_marker = "defined"
define startup_order = []

init python:
    startup_order.append("init_default")

init 100 python:
    startup_order.append("init_100")

label start:
    $ emit("startup_state",
           marker=startup_marker,
           order=list(startup_order),
           has_start=renpy.has_label("start"))
    "startup chain reached start"
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

testcase startup_reach:
    $ arm()
    run Jump("start")
    advance until screen "say"
    screenshot "startup_at_start"
    $ shot("startup_at_start")
    advance
    exit