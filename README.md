## Project plan


### Group members

|     Name           |              Email               |      ID#       |
| ------------------ | -------------------------------- | -------------- |
| Mikko Esko         | mikko.esko@student.tut.fi        |     246182     |
| Teemu Salminen     | teemu.2.salminen@student.tut.fi  |     266987     |

You can view the deployed project on https://morning-taiga-86071.herokuapp.com/

In order to try out and test some aspects of the work you can create new account, or you can use one of existing ones:

* Credentials for developer: Username: user1 Password: test2236 
* Login Credentials for player: Username: user2 Password: test2236 

### Listed features

##### User Registration and Login (Teemu)
 * Register an user
 * Login/logout
   * Login and logout handled using Django Authentication System
 * Email validation (using mock-up because we don't have a mail server)

##### Basic player functionalities (Teemu)
 * Buy games
 * Play games
 * Security (allow players to only play games they've made or purchased)
 * Search for games/developers by name/tags

##### Developer functionalities (Mikko)
 * Add/modify games
    * Games have url, name, price
    * Optionally tags, description, logo, banner
 * Game inventory
 * Sales statistics
    * Sales are visible on developer dashboard
 * Security (developers are only allowed to modify their own games)

##### Game/service interaction (Mikko/Teemu)
 * Game and the game service communicate with window.postMessage
 * SETTING, SCORE, SAVE, LOAD, LOAD_REQUEST and ERROR postMessages

##### Non-functional 
 * Project plan (all)

##### JavaScript games
 * 3 JavaScript games (everyone makes one)
    * Sudoku Shooter (Mikko)
    * Single player pong (Teemu)
 * Games implement the save/load/score/setting features

### Extra features

* Reviews (Teemu)
* JSON API (Mikko)
    * List of games
        * by tags
    * Sales
        * only accessible by developer of the game
        * query by game id and time of purchase
    * High score
        * query by game
        * can also choose how many highest scores to show
* Testing the service with other group's games (Mikko)
    * Test service with multiple games made by other groups
    * 3 games tested in-depth and reviewed


### Views (Teemu/Mikko)
* Bootstrap for the frontend
* Main page template
    * Search bar
    * Navi bar
        * Links to store, dashboard
        * Login/Logout/Register links
* Login page
    * Form to login
    * Link to register
* Register page
    * Form to register
* Adding a game
    * Form to submit a game
* Game view
    * Description of the game
    * Reviews
    * Option to purchase/play
* Play view
    * Name of the game
    * The game in an iframe
    * Description of the game
    * High scores
* Player dashboard
    * Shows which games the player owns
* Developer dashboard
    * Uploaded games
    * Game sales


### Models (Mikko/Teemu)
* User
* Game
* PurchasedGame
    * Date of purchase
    * Saved game states
    * Highscore
* Sale
* Tag
* Review
    * a star rating (not implemented)
    * text review


### Plan
Project plan was made in a meeting face-to-face. Afterwards communication was primarily through Slack. We also used Gitlab's issues to keep track of the project's state and divide the work.

### Retrospect

#### Successes
* The store ended up being somewhat responsive and looking quite nice, mostly because we used Bootstrap.

#### Problems
* I think we used more templates than necessary which is bad for maintainability
* Different Bootstrap versions (3.3 vs 4) made browsing the documentation a pain.
* There were many minor features we planned to implement but didn't for various reasons. Maybe we should have been more thorough in the planning phase.
* Not committing/pushing migrations to the repository regularly caused some problems with the database.
