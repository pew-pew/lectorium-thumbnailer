"use strict";

let avaliableTemplates = null;
let thumbnailers = null;

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function createApp(element, params) {//, thumbnailerTemplate) {
    let app = new Vue({
        el: element,
        data: {
            subject: "",
            topic: "",
            number: "",
            template: null,
            fontSize: 70,

            thumbnail: null,
            videoId: null,

            thumbnailURL: 'https://placehold.it/550x550',

            ...params
        },
        computed: {
            avaliableTemplates: function() {
                let isGood = ({subject}) => (subject.toLowerCase().includes(this.subject.toLowerCase()));
                return [...avaliableTemplates.filter(isGood),
                        ...avaliableTemplates.filter((templ) => !isGood(templ))];
            },
        },
        watch: {
            subject:  function () { saveExportsThrottled(); },
            template: function () { saveExportsThrottled(); this.reloadThumbnail(); },
            fontSize: function () { saveExportsThrottled(); this.reloadThumbnail(); },
            number:   function () { saveExportsThrottled(); this.reloadThumbnailDebounced(); },
            topic:    function () { saveExportsThrottled(); this.reloadThumbnailDebounced(); },
        },
        created: function () {
            this.reloadThumbnail();
            this.reloadThumbnailDebounced = _.debounce(this.reloadThumbnail, 500);
        },
        methods: {
            genThumbnailURL: function() {
                if (this.template === null)
                    return 'https://placehold.it/550x550';
                return "http://localhost:8888/thumbnail?" + (new URLSearchParams({
                    number: this.number,
                    topic: this.topic,
                    template: this.template,
                    fontSize: this.fontSize,
                    videoId: this.videoId
                })).toString()
            },
            reloadThumbnail: async function () {
                this.thumbnailURL = this.genThumbnailURL();
                // if (this.template === null)
                //     return;

                // console.log(
                //     `Reloading thumbnai: (${this.videoId}) ${this.subject} # ${this.number} [${this.template}]`
                // );

                // let resp = await (await fetch("http://localhost:8888/thumbnail", {
                //     method: "POST",
                //     body: JSON.stringify(this.$data),
                // })).json();

                // console.log(resp);
                // console.log("Done!");

                // this.thumbnail = resp + "?q=" + (this.counter++);
            }
        }
    });
    return app;
}


async function main_test() {
    let thumbnailerTemplate = await loadTemplate("template.html");

    avaliableTemplates = await (await fetch("http://localhost:8888/templates/list")).json();
    let exports = await (await fetch("http://localhost:8888/exports/get")).json();

    let videos = {
        "abcdef": {
            subject: "subject1",
            topic: "kafka",
            number: 123,
        },
        "xyzuvw": {
            subject: "subject2",
            topic: "integralyyyyy",
            number: 567,
        },
    };

    for (let i = 0; i < 1; i++) {
        videos[i + ""] = {
            subject: "мат",
            topic: "hey",
            number: 20
        }
    }

    exports = {...videos, ...exports};

    thumbnailers = Object.entries(exports).map(([videoId, video]) => {
        return createApp(document.body.appendChild(thumbnailerTemplate.cloneNode(true)), {
            ...video,
            videoId: videoId
        });
    });

    saveExports();
}

async function main_yt() {
    await sleep(3000);

    let thumbnailerTemplate = await loadTemplate(browser.runtime.getURL("template.html"));

    avaliableTemplates = await (await fetch("http://localhost:8888/templates/list")).json();
    let exports = await (await fetch("http://localhost:8888/exports/get")).json();

    thumbnailers = [];

    Array.from(document.getElementsByTagName("ytd-playlist-video-renderer")).forEach(videoEl => {
        let title = videoEl.querySelector("#video-title").textContent.trim();
        let content = videoEl.querySelector("#content");          
        let videoUrl = new URL(content.querySelector(":scope > a").href);
        let videoId = videoUrl.searchParams.get("v");
        let match = title.match(
          /^([^\d,.]*)([,.]\s*семинар)?\s*(\d+)\.(.*)$/i
        );
        
        let params = {};
        if (match !== null) {
            var [_, subject, sem, number, topic] = match;

            params = {
                subject: subject.trim(),
                number: parseInt(number.trim()),
                topic: topic.trim(),
            }
        }

        if (videoId in exports)
            params = {...params, ...exports[videoId]}

        let el = thumbnailerTemplate.cloneNode(true);
        content.appendChild(el);
        thumbnailers.push(createApp(el, {
            ...params,
            videoId: videoId
        }));
    });

    saveExports();
}

async function saveExports() {
    let exports = _.fromPairs(thumbnailers.map(app =>
        [app.videoId, {
            subject: app.subject,
            topic: app.topic,
            number: app.number,
            template: app.template,
        }]
    ))

    console.log("Saving exports...");

    await fetch("http://localhost:8888/exports/set", {
        method: "POST",
        /* TODO: learn how to handle preflight cors requests
        headers: {
            "Content-Type": "application/json"
        },
        */
        body: JSON.stringify(exports),
    });

    console.log("Saved!");
}

let saveExportsThrottled = _.throttle(saveExports, 1000);
// main_test();
main_yt();

console.log("HELLO");

async function loadTemplate(url) {
    console.log(url);
    let text = await (await fetch(url)).text();
    let el = document.createElement("template");
    el.innerHTML = text.trim();
    return el.content.firstChild;
}