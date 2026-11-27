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
    def audio_state():
        return {
            "music": renpy.music.get_playing("music"),
            "sound": renpy.music.get_playing("sound"),
        }

label start:
    $ emit("audio_initial", **audio_state())
    play music "audio/tone.ogg" fadein 0.1
    $ emit("audio_playing", **audio_state())
    play sound "audio/tone.ogg"
    $ emit("audio_sound_playing", **audio_state())
    stop sound
    $ emit("audio_sound_stopped", **audio_state())
    stop music
    $ emit("audio_music_stopped", **audio_state())
    "audio checked"
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

testcase audio_lifecycle:
    $ arm()
    run Jump("start")
    advance until screen "say"
    advance
    $ disarm()
    exit
