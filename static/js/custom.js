MathJax = {
    tex: {
        displayMath: [['\\[', '\\]'], ['$$', '$$']],  // block
        inlineMath: [['\\(', '\\)'], ['$', '$']]                  // inline
    },
    startup: {
        pageReady: () => {
            return MathJax.startup.defaultPageReady();
        }
    }
};