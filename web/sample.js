async function main() {
    text = await (await fetch(browser.runtime.getURL("template.html"))).text();
    
}
main()