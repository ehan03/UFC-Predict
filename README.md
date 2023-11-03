# UFC-Predict

_Applying machine learning and optimization techniques to the UFC_


TO-DO: MIGRATE TO PLANETSCALE (big code changes needed)
- Create relevant tables in CLI, make sure to include bout ordinals as a column for ORDER BY statements
- Figure out sqlalchemy
- Rework entire set of Scrapy pipelines to follow new paradigm

As of writing, the project leverages data from the following sources:
- [UFC Stats](http://ufcstats.com/statistics/events/completed): Bout and fighter statistics
- [Tapology](https://www.tapology.com/fightcenter): Bout and fighter statistics, some of which are not available on the UFC Stats website
- [UFC Rankings](https://www.ufc.com/rankings): Fighter rankings
- [FightOdds.io](https://fightodds.io/upcoming-mma-events/ufc): Betting odds

---
*This project is actively in development and a huge WIP. As such, the README will be updated accordingly.*
