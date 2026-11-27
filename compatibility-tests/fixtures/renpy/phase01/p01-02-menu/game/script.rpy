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

default choice_log = []

label start:
    menu:
        "Option A":
            $ choice_log.append("A")
            $ emit("choice_taken", which="A")
            "chose A"
        "Option B":
            $ choice_log.append("B")
            $ emit("choice_taken", which="B")
            "chose B"
    $ emit("after_first_menu", log=list(choice_log))
    "after first menu"
    menu:
        "outer":
            menu:
                "inner one":
                    $ choice_log.append("inner-one")
                    $ emit("nested_choice_taken", log=list(choice_log))
                    "inner one chosen"
    $ emit("after_nested_menu", log=list(choice_log))
    "after nested menu"
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

testcase menu_choose_b:
    $ arm()
    run Jump("start")
    advance until screen "choice"
    screenshot "menu_choice_shown"
    $ shot("menu_choice_shown")
    click "Option B" always
    advance until screen "say"
    advance
    exit

testcase menu_nested:
    $ arm()
    run Jump("start")
    advance until screen "choice"
    click "Option A" always
    advance until screen "say"
    advance until screen "choice"
    click "outer" always
    advance until screen "choice"
    click "inner one" always
    advance until screen "say"
    advance
    exit