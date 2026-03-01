---
layout: post
title: "Kernel smoothing for calibration estimation"
date: "2026-03-01 17:35"
thumbnail_path: 'blog/2025-12-21-kernel-smoothing/thumbnail.png'
extra_scripts:
- https://cdn.plot.ly/plotly-3.3.0.min.js
tags:
- Calibration
- Visualisation
---

I'll show some early calibration plots of my calibration tracking, and show how I've used a few smoothing techniques to produce useful early charts.

# Intro

I like making quantified predictions (perhaps more on that another time). These look like either "I'm X% sure Y will happen" or "I'm X% sure the value of Y will between A and B".

My current interest is calibrating these predictions (i.e. getting that X% to reflect reality as closely as possible - i.e. on average 90% of the things I say are 90% likely should happen). I've started recording my predictions (with confidence bounds), and I'd like to start visualising my calibration curve.

Unfortunately, this data is pretty sparse (currently 22-ish predictions, spread from 50% to 95%)[^right-hand]. The outcome of each of these is binary (i.e. the actual value was either in my prediction bands, or not).

I'll probably write more about prediction calibration in general at some point. This post just covers early visualisations of it, and the required smoothing.

I'm a big proponent of producing and maintaining confidence bounds, so this is a good opportunity to do this.

# Aim


By the end of this post, I want a chart showing my calibration curve, with reasonable[^reasonable] confidence bounds. This will give me an early read on my calibration, and allow me to start making adjustments as soon as possible. 
And as a bonus, as the number of samples I have grows, the confidence bounds should shrink, in a way that will allow me to use this calibration curve as a lookup table to answer questions like: "When I say 90%, I mean X%, with confidence intervals P and Q".

# The raw data

I have a set of predictions. Each of them has a confidence attached. I can then evaluate whether the actual outcome was within the confidence or not.
There are two kinds of predictions:
1. **Numerical** - I predict the numerical range of some thing, with confidence bounds. This has the form: <br>
"I'm $x$% sure that the value of $y$ is between $a$ and $b$." 
<br>e.g. (while on a trip to Copenhagen) "I'm 70% sure the distance from where we are to our accomodation is between 4km and 8km".[^1]
2. **Boolean** - I predict whether something is true or false, with some confidence. <br>
This has the form: "I'm $x$% sure that $y$ is true". <br>
e.g. (on a trip to Florence) "I'm 95% sure that a Bialetti Moka pot will be for sale at the Florence Airport when we fly out".[^2]

Let's have a look at what this raw data looks like:

{% include plotly-chart.html id="raw-data" json="/assets/viz/kernel-smoothing/chart_1.json" %}

The blue dots show the actual outputs (1 for True - when the true outcome was within my confidence band and 0 for False - when the true outcome was outside of my confidence band). I've added a little jitter so that we can see the points.

In red are the averages per confidence level - they give my average success rate. Now, if there were a lot of samples, these would likely approach the true underlying success rate, but my data is really sparse!

# Distribution of belief at each confidence level

So, we might like to look the distribution of our belief in what the true success rates are. We can do this by specifying a prior, and then applying Bayesian updates to get a posterior[^3]. I've used a uniform prior here, and modelled this as a Beta distribution[^4]. Here are the posteriors we get for each confidence level, plotted as a Ridgeline plot:

{% include plotly-chart.html id="beta-with-uniform-prior" json="/assets/viz/kernel-smoothing/chart_2.json" %}

This feels a little more useful. We can see that our confidence in the true success rates are pretty low (given that the distributions are spread out). A few things to note:
- The MAP (maximum a priori) estimate matches the success rate - this is the most likely value (the max point of each distribution), given the evidence, which feels right.
- There's no obvious trend across the prediction confidence levels.

# Finding a trend

This allows me to make a rough statement like "When I say 50%, the true likelihood is in the region of 40% and 95%". And as I record more 50% predictions, this range will narrow. But, it doesn't allow me to say anything about when I make a prediction at 55%.
Is it like 50%, 60%? Something in between?

Let's try some basic smoothing. A (hopefully uncontroversial) assumption here is that my calibration curve should be reasonably smooth (i.e. the true success rates for nearby confidence levels should be similar).

How should we smooth it? We could do a basic moving average maybe (i.e. look left and right 10% and average these points)? This would probably work okay-ish, but would still fail when we're in an especially sparse region.

Something we need to confront - how strong should the smoothness be? How much influence should closer points have on the resulting estimate? I don't know of any principled ways to do this, so we'll just need to try a few things out, and see what feels right.

To start, let's just use an RBF (Radial Basis Function) kernel to smooth the values. An RBF kernel is really just a Gaussian distribution, with a variance ($\sigma^2$) of what I call here the 'bandwidth'.

{% include plotly-chart.html id="kernel-snmoothing" json="/assets/viz/kernel-smoothing/chart_3.json" %}

You can play with the slider to see what changes as we change the bandwidth. We can see that the confidence bounds are always pretty wide. As we increase the bandwidth, the line flattens out (and it becomes closer to just a global average).

Let's see what this looks like when we include a prior that I'm perfectly calibrated. Then, as new evidence arrives, this posterior will update.


{% include plotly-dual-slider.html id="chart4" json="/assets/viz/kernel-smoothing/chart_4.json" n_bw=12 n_prior=7 %}

You can now use both sliders to see the effect of the combination. As the strength of the prior increases, the resulting calibration curve is forced closer to $y=x$, and the confidence bounds narrow.

Now, I don't think that a prior of this form is eactly right - we'd probably prefer a prior on some kind of monotonicity, but this is probably fit for purpose.

Without a lot of reasoning, I'm going to pick a bandwidth of 0.05 and prior of 0.1 for now.

# Conclusion

I now have a workable smoothing technique, which gives me an early glimpse of my calibration curve (which is for now very noisy, and not very useful).

Once I have some more scored predictions, I'll add a new post showing how the calibration curve evolves over time.

# Footnotes 

[^1]: It was 3.2km away - not a good start here for my first prediction!
[^2]: None to be found - you know how hard is to come back from your first 95% prediction being wrong?
[^3]: I could really pick any prior, based on my belief about how well calibrated I am - a uniform prior is saying "I have no prior belief about how well calibrated I am at this level - I'd be as unsuprised if I were always right, always wrong, or any other consistent outcome". This doesn't feel *quite* right, since I expect to be *roughly* calibrated at least. More on this to follow.
[^4]: The beta distribution here assumes that the outcomes at each level are governed by a Bernoulli trial. This assumes that at each level there is one probability $p$ which is driving the boolean outcomes. I'm not sure this is reasonable - if I'm not perfectly calibrated, it's not likely the case that I'm just swapping confidence levels (i.e. when I say 90%, I actually *always* mean 80%). It's more likely that when I say 90%, I sometimes mean 60%, sometimes 70% etc. My intuition is that this will all net out somewhere (and I think this is a necessary assumption to make this problem tractable).
[^reasonable]: For *some* definition of reasonable. 
[^right-hand]: If I make a prediction with a confidence lower than 50%, I reflect it and invert the criteria (so 20% True becomes 80% False, etc).
