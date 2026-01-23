document.querySelectorAll('img.inline-svg').forEach(el => {
    fetch(el.src).then(r => {
        r.text().then(c => {
            const doc = (new DOMParser()).parseFromString(c, 'text/xml');
            const svg = doc.querySelector('svg');
            svg.id = el.id || svg.id
            // svg.classList = el.classList || svg.classList;
            el.classList.forEach(cl => svg.classList.add(cl));
            // need to remove "xmlns:a" attr?
            // width/height are not useful
            svg.setAttribute('width', '');
            svg.setAttribute('height', '');
            console.log(svg.width, svg.height);
            el.replaceWith(svg);
        });
    });
});