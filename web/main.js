"use strict";


let thumbnailers = null;


function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function loadTemplate(url) {
    console.log(url);
    let text = await (await fetch(url)).text();
    let el = document.createElement("template");
    el.innerHTML = text.trim();
    return el;
}

function parseInfoFromTitle(title) {
    const match = title.match(
      /^([^\d,.]*)([,.]\s*семинар)?\s*(\d+)\.(.*)$/i
    );

    if (match === null)
        return null;

    const [_, subject, sem, number, topic] = match.map(s => s && s.trim());
    return {subject, number, topic};
}

async function saveExports() {
    let exportsDict = _.fromPairs(thumbnailers.map(app =>
        [app.videoId, {
            subject: app.subject,
            topic: app.topic,
            number: app.number,
            template: app.template,
            fontSize: app.fontSize,
        }]
    ));

    // console.log("Saving exports...");

    await fetch("http://localhost:8888/exports/set", {
        method: "POST",
        /* TODO: learn how to handle preflight cors requests
        headers: {
            "Content-Type": "application/json"
        },
        */
        body: JSON.stringify(exportsDict),
    });

    // console.log("Saved!");
}

let saveExportsThrottled = _.throttle(saveExports, 1000);


// Because template is loaded separetely (webpack/other things are out of my sight)
async function createThumbnailerComponent() {
    return Vue.component("thumbnail-editor", {
        template: await loadTemplate(browser.runtime.getURL("template.html")),
        props: {
            avaliableTemplates: {default: [], required: true},
            videoElement: {required: true},
            videoId:  {required: true},
            subject:  {default: ""},
            topic:    {default: ""},
            number:   {default: ""},
            template: {default: null},
            fontSize: {default: 70},
        },
        data: function() {
            return {
                thumbnailURL: null, // will be set by `created()`
                loading: false,
            }
        },
        created: function () {
            this.reloadThumbnailDebounced = _.debounce(this.reloadThumbnail, 500);
            this.reloadThumbnail();
        },
        watch: {
            subject:  function () { saveExportsThrottled(); },
            template: function () { saveExportsThrottled(); this.reloadThumbnail(); },
            fontSize: function () { saveExportsThrottled(); this.reloadThumbnail(); },
            number:   function () { saveExportsThrottled(); this.reloadThumbnailDebounced(); },
            topic:    function () { saveExportsThrottled(); this.reloadThumbnailDebounced(); },
            thumbnailURL: function() { this.loading = true; },
        },
        computed: {
            sortedAvaliableTemplates: function() {
                let isGood = ({subject}) => (subject.toLowerCase().includes(this.subject.toLowerCase()));
                return [...this.avaliableTemplates.filter(isGood),
                        ...this.avaliableTemplates.filter((templ) => !isGood(templ))];
            },
            spinnerURL: () => (browser.runtime.getURL("spinner.gif"))
        },
        methods: {
            genThumbnailURL: function() {
                if (this.template === null)
                    return "https://placehold.it/1920x1080";
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
            },
            thumbnailLoaded: function() {
                this.loading = false;
            },
            // TODO: refactor
            parse: function() {
                const title = this.videoElement.querySelector("#video-title").textContent.trim();
                const info = parseInfoFromTitle(title);
                if (info === null)
                    return;
                this.number = info.number;
                this.subject = info.subject;
                this.topic = info.topic;
            },
            upload: async function() {
                console.log("UAWDAWD")
                if (this.template === null)
                    return;
                let resp = await fetch("http://localhost:8888/upload", {
                    method: "POST",
                    body: JSON.stringify({
                        number: this.number,
                        topic: this.topic,
                        template: this.template,
                        fontSize: this.fontSize,
                        videoId: this.videoId,
                    }),
                });
                console.log(resp);
                console.log(await resp.json());
            }
        }
    });
}

async function main() {
    // cleanup existing widgets
    document.querySelectorAll(".lt-container").forEach(el => el.remove())    

    const thumbnailerComponent = await createThumbnailerComponent();

    let avaliableTemplates = await (await fetch("http://localhost:8888/templates/list")).json();
    let exportsDict = await (await fetch("http://localhost:8888/exports/get")).json();

    // let avaliableTemplates = [];
    // let exportsDict = [];

    let videoElements = Array.from(document.getElementsByTagName("ytd-playlist-video-renderer"));
    thumbnailers = videoElements.map(videoEl => {
        const title = videoEl.querySelector("#video-title").textContent.trim();
        const contentEl = videoEl.querySelector("#content");
        const videoUrl = new URL(contentEl.querySelector(":scope > a").href);
        const videoId = videoUrl.searchParams.get("v");

        const info = {...parseInfoFromTitle(title), ...exportsDict[videoId]};

        let thumbnailer = new thumbnailerComponent({
            propsData: {
                ...info,
                videoElement: videoEl,
                avaliableTemplates: avaliableTemplates,
                videoId: videoId,
            }
        });

        const mountPoint = contentEl.appendChild(document.createElement("div"));
        thumbnailer.$mount(mountPoint);
        return thumbnailer;
    });
}


main();