# README

This repo provides the code for rfishermonteith.github.io

It is heavily based on https://www.ybrikman.com/ and https://github.com/brikis98/yevgeniy-brikman-homepage/

## Tracking

I'd like very simple tracking, just to know which posts are read, when.
I initially tried Google Analytics, which is very easy to set up, and provides great analytics, but requires a cookie notice and consent for the EU ePrivacy Directive, which is:
1. Difficult/complex to implement for Jekyll
1. Unnecessarily creepy for a personal blog (and I don't want to have ask for cookie consent)

So, an alternative is [piratepx](https://www.piratepx.com/), which:
1. Doesn't require any cookies
1. Only tracks anonymised pageviews (and potentially other custom events - also anonymised)
1. Requires a 1-line piece of code

See https://www.felixparadis.com/posts/piratepx-review-analytics-without-js-cookies-or-legal-headache/ for more details (and some nice meta/dogfooding).

## Running locally

Run `docker compose up` from the root directory to build and run a docker image which will serve the webiste locally. This will also watch for changes and automatically restart the server to serve them.
