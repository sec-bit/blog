# 🌈➕🐎➡️🦄 SECBIT Blog

👉👉👉 ***https://sec-bit.github.io/blog*** 👈👈👈

## Usage

- Write: in `content/post` folder
- Preview: `hugo server -D`
- ~~Publish: `./publish_to_ghpages.sh` and `git push --all`~~
- Git commit and push to the `master` branch, GitHub Actions will build and deploy the site automatically.

## More

- Hugo Static Site Generator hugo v0.136.5+extended
- https://gohugo.io/getting-started/usage/
- Cloudflare Rocket Loader should be disabled for this site or the MathJax will not work.

## Software Versions

The GitHub Actions [workflow](https://github.com/sec-bit/blog/blob/master/.github/workflows/hugo.yml#L34-L44) uses the following software versions:

```
hugo v0.147.9
pandoc 3.7.0.2
```

Use the same software versions to build and preview the site locally.