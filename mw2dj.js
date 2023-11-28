// ==UserScript==
// @name         Merriam-Webster to Daniel Jones Phonetic Converter
// @namespace
// @version      0.1
// @description  Convert Merriam-Webster phonetic symbols to Daniel Jones phonetic symbols.
// @author       WANG Lei
// @match        https://www.merriam-webster.com/dictionary/*
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant        none
// ==/UserScript==

(function () {
    "use strict"

    const show_webster = true

    function convertPhoneticSymbol(mw) {
        const nwt = mw.trim()
        let t = nwt

        t = t.replaceAll("ər", "ɚ") // further, merger, bird

        t = t.replaceAll("ȯi", "ɔɪ") // coin, destroy

        t = t.replaceAll("i", "ɪ") // tip, banish, active

        t = t.replaceAll("e", "ɛ") // bet, bed, peck

        t = t.replaceAll("ō", "oʊ") // bone, know, beau

        t = t.replaceAll("ȯ", "ɔː") // saw, all, gnaw, caught

        t = t.replaceAll("u̇", "ʊ") // pull, wood, book
        t = t.replaceAll("ü", "uː") // rule, youth, union, few

        t = t.replaceAll("a", "æ") // mat, map, mad, gag, snap, patch

        t = t.replaceAll("au̇", "aʊ") // now, loud, out
        t = t.replaceAll("æʊ", "aʊ")

        t = t.replaceAll("ī", "aɪ") // site, side, buy, tripe

        t = t.replaceAll("ā", "eɪ") // day, fade, date, aorta, drape, cape

        t = t.replaceAll("ä", "ɑː") // bother, cot

        // consonants
        t = t.replaceAll("sh", "ʃ") // shy, mission, machine, special
        t = t.replaceAll("zh", "ʒ") // vision, azure
        t = t.replaceAll("j", "dʒ") // job, gem, edge, join, judge
        t = t.replaceAll("ch", "tʃ") // chin, nature
        t = t.replaceAll("th", "θ") // thin, ether
        t = t.replaceAll("t͟h", "ð") // then, either, this
        t = t.replaceAll("y", "j") // yard, young, cue, curable, few, fury, union

        t = t.replaceAll("ᵊl", "l̩") // bottle
        t = t.replaceAll("ᵊm", "m̩") // open
        t = t.replaceAll("ᵊn", "n̩") // cotton
        t = t.replaceAll("ᵊŋ", "ŋ̍") // and

        // 特殊处理
        let syllables = t.split("-")
        let new_syllables = []
        for (let i = 0; i < syllables.length; ++i) {
            let s = syllables[i]
            if (isStress(s[0])) {
                s = s.replaceAll("ē", "iː") // beat, nosebleed, evenly, easy
                s = s.replaceAll("ə", "ʌ") // humdrum, abut
            } else {
                s = s.replaceAll("ē", "i") // easy, mealy
            }
            new_syllables.push(s)
        }
        t = new_syllables.join("-")

        if (show_webster) {
            return nwt + " | " + t + "\u00A0"
        }
        return t + "\u00A0"
    }

    function isStress(c) {
        return c == String.fromCharCode(712) || c == String.fromCharCode(716)
    }

    $(document).ready(function () {
        let pron1 = Array.from(document.getElementsByClassName("play-pron-v2"))
        pron1.map((e) => {
            e.firstChild.data = convertPhoneticSymbol(e.firstChild.data)
        })

        let pron2 = Array.from(document.getElementsByClassName("mw"))
        pron2.map((e) => {
            e.textContent = convertPhoneticSymbol(e.textContent)
        })
    })
})()
