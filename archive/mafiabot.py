import asyncio
import discord
from dotenv import load_dotenv
import random
import time
from openai import OpenAI
import os
# from predictorAI import PredictorAI


load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure OpenAI client
# openai_client = OpenAI(base_url="https://oai.hconeai.com/v1", api_key=os.getenv("OPENAI_API_KEY"))
openai_client = OpenAI(base_url="https://api.openai.com/v1", api_key=os.getenv("OPENAI_API_KEY"))


# Define intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.dm_messages = True

openai = discord.Client(intents=intents)

activity = discord.Game(name="m!help")


@openai.event
async def on_ready():
    await openai.change_presence(status=discord.Status.idle, activity=activity)

    for guild in openai.guilds:
        if 'Mafia' not in [role.name for role in guild.roles]:
            await guild.create_role(name='Mafia')
        role = discord.utils.get(guild.roles, name='Mafia')
        found = []
        for channel in guild.channels:
            if channel.name == 'mafia' or channel.name == 'Mafia':
                found.append(channel.type)
        if discord.ChannelType.text not in found:
            await guild.create_text_channel('mafia')
        if discord.ChannelType.voice not in found:
            await guild.create_voice_channel('Mafia')
        for channel in guild.channels:
            if channel.name == 'mafia' or channel.name == 'Mafia':
                await channel.set_permissions(guild.default_role, read_messages=False)
                await channel.set_permissions(role, read_messages=True)


commands = {
    'help': '`m!help` displays the help screen. Fairly obvious.',
    'h2p': '`m!h2p` describes the basic rules and premise of the game.',
    'start': '`m!start` begins a new round of mafia.',
    'end': '`m!end` ends the current game, if existing. Can only be called by a moderator or a player.',
    'roles': '`m!roles` lists all available roles that can be added to the game.',
    'set': '`m!set [role] [number]` sets the quantity of `[role]` in the setup to `[number]`. e.g. `m!set villager 3`',
    'setup': '`m!setup` shows the full complement of roles in the current setup.',
    'settings': '`m!settings` displays all the settings of the current game.',
    'toggle': '`m!toggle [setting]` flips `[setting]` from on to off, or vice versa. Type `m!settings` to see options. e.g. `m!toggle daystart`',
    'setlimit': '`m!setlimit [phase] [time]` sets the time limit for `[phase]` to `[time]` in minutes. `[time]` can be a positive real number at least 1 or `inf`. e.g. `m!setlimit day 10`',
    'join': '`m!join` adds you to the game.',
    'leave': '`m!leave` removes you from the game. This may end an ongoing game, so be careful using this command.',
    'vote': '`m!vote [player]` puts your current vote on `player`. Vote this bot to set your vote to no-lynch. e.g. `m!vote @mafiabot`',
    'unvote': '`m!unvote` sets your vote to nobody (no vote).',
    'status': '`m!status` displays all players and their votes, as well as the vote count on each player.',
    'players': '`m!players` displays all players who are currently alive',
    'alive': '`m!alive` displays all the roles and their quantities that are still in play.',
    'dead': '`m!dead` displays the players in the graveyard and their roles (if roles are revealed upon death).',
    'time': '`m!time` displays the amount of time left, before the day or night ends.',
    'testPredict': '`m!testPredict` tests the predictorAI object.',
    'testState': '`m!testState` tests the state of the predictorAI object.',
    'test1': '`m!test1` tests the chatgpt model and prediction',
}

help_text = [
    "```List of commands```",
    "Type `m!help [command]` to receive details about the command itself.",
    "**1. Basic**: `help` `h2p` `start` `end`",
    "**2. Setup**: `roles` `set` `setup` `settings` `toggle` `setlimit` `join` `leave`",
    "**3. In-game**: `vote` `unvote` `status` `players` `alive` `dead` `time` `predict` "
]

h2p_text = [
    "**How to play:**",
    "Mafia is a party game in which all the players are split into two opposing factions: the innocent villagers and the guilty mafia.\n",
    "The game alternates between two phases:",
    "1. Daytime, when players can discuss and debate the identity of the mafia. Players can also majority vote to lynch one member of the community who they suspect of being guilty.",
    "\t- If the day timer reaches its time limit, a no-vote is considered equivalent to a no-lynch vote.",
    "\t- Otherwise, daytime ends when all players have voted (regardless of if majority is reached before).",
    "2. Nighttime, when mafia are free to murder one innocent citizen of the town, and certain townspeople can use their special abilities.\n",
    "If you are a villager, your win condition is to identify and lynch all of the mafia.",
    "If you are a mafia, your win condition is to either equal or outnumber the townspeople.",
    "At the start of the game, your role will be assigned to you via DM by this bot.\n",
    "NOTE: It is recommended to mute pings from this bot, since `@'s` are necessary to properly identify players."
]

roles_text = [
    "**Roles:**",
    "`villager`: Village-aligned role. No special powers.",
    "`normalcop`: Village-aligned role, capable of determining the alignment of a target player during nighttime.",
    "`paritycop`: Village-aligned role, capable of determining whether his LAST TWO targets are of the same alignment (will not get a report after night 1).",
    "`doctor`: Village-aligned role, capable of saving a target player from death during nighttime.",
    "`mafia`: Mafia-aligned role. Capable of killing a villager during nighttime with fellow mafia."
]

toggle_text = [{
    'daystart': '`daystart` toggled off: The game will commence during nighttime.',
    'selfsave': '`selfsave` toggled off: Doctors will not be able to save themselves during nighttime.',
    'conssave': '`conssave` toggled off: Doctor will not be able to save the same patient over consecutive nights.',
    'continue': '`continue` toggled off: The game will end if a living player quits.',
    'reveal': '`reveal` toggled off: When a player dies, their role will not be revealed.'
}, {
    'daystart': '`daystart` toggled on: The game will commence during daytime.',
    'selfsave': '`selfsave` toggled on: Doctors will be able to save themselves during nighttime.',
    'conssave': '`conssave` toggled on: Doctor will be able to save the same patient over consecutive nights.',
    'continue': '`continue` toggled on: The game will not end if a living player quits.',
    'reveal': '`reveal` toggled on: When a player dies, their role will be revealed.'
}]

end_text = {
    'None': 'Nobody wins!',
    'Mafia': 'The mafia win!',
    'Town': 'The villagers win!'
}

class PredictorAI:
    def __init__(self, players):

        # Keep track of the current players in the game. Dictionary object.
        self.players = players

        # Keep track of the deaths: List of tuples (Round, Player Object)
        self.deaths = []

        # Keep track of the world facts
        self.world_facts = []

        self.round_descriptions = {} # 0: [[' hey what's  up hello'], [' hey what's  up hello'], [' hey what's  up hello']]
        self.predictions = [] # A list of predictions after each .round.



class Player:
    def __init__(self, id, server):
        self.id = id
        self.alive = 1
        self.role = None
        self.vote = None
        self.server = server
        self.ingame = 1  # changes to 0 upon m!leave, will be removed from server.players upon game end
        self.options = []  # nighttime options for power role
        self.action = 0  # if a power role, if has performed night action or not
        self.cur_choice = None  # if a power role, their choice for the night
        self.lst_choice = None  # if parity cop, last choice


class Server:
    def __init__(self):
        self.players = {}  # dictionary mapping player IDs to a Player class
        self.running = 0
        self.phase = 0  # 0 for night, 1 for day
        self.actions = 0  # how many actions remain during nighttime
        self.time = 0  # how much time remains in the phase
        self.round = 0  # what day/night of the game it is (e.g. day 1, night 2, etc)
        self.saves = []  # list of doctor saves (by ID)
        self.settings = {
            'daystart': 0,  # game starts during daytime
            'selfsave': 0,  # doctor can save themselves
            'conssave': 0,  # doctor can save the same person in consecutive turns
            'continue': 0,  # continue playing even if a player leaves
            'reveal': 0,  # reveal role of player upon death
            'limit1': 'inf',  # time limit for days
            'limit2': 'inf'  # time limit for nights
        }
        self.setup = {
            'villager': 0,
            'normalcop': 0,
            'paritycop': 0,
            'doctor': 0,
            'mafia': 0
        }
        self.predictorAI = None
        # self.predictorAI = PredictorAI() # Initialize this new object to store player knowledge and actions.


power_roles = ['normalcop', 'paritycop', 'doctor', 'mafia']

servers = {}  # dictionary mapping server IDs to server class
# new server class will be created whenever bot is run in server

allPlayers = {}  # dictionary mapping player IDs to server they're playing in


# player removed when m!leave


# TODO: remove this test_gpt_joke function (just for testing openai connection)
async def test_gpt_joke(message, word):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "A user requests a joke. Say a funny joke about %s." % word,
                }
            ],
            temperature=1,
            max_tokens=256,
            top_p=1
        )
        joke = response.choices[0].message.content
        # print("Joke response:", joke)
        await message.channel.send(joke)
    except Exception as e:
        await message.channel.send("Sorry, I couldn't generate a joke right now. Please try again later.")
        print(e)  # For debugging


async def death(channel, player, server):
    server.players[player].alive = 0
    if server.settings['reveal']:
        await channel.send('Their role was `%s`.' % server.players[player].role)


async def game_end(channel, winner, server):  # end of game message (role reveal, congratulation of winners)
    server.running = 0
    await channel.send('\n'.join(
        [end_text[winner]] + ['The roles were as follows:'] + ['<@%s> : `%s`' % (player.id, player.role) for player in
                                                               server.players.values()]))
    for key in server.players:
        if not server.players[key].ingame:
            server.players.pop(key)


async def check_end(channel, server):
    if not sum([player.role == 'mafia' for player in server.players.values() if player.alive]):  # no mafia remaining
        await game_end(channel, 'Town', server)
        return 1
    elif sum([player.role == 'mafia' for player in server.players.values() if player.alive]) >= sum(
            [player.role != 'mafia' for player in server.players.values() if player.alive]):
        await game_end(channel, 'Mafia', server)
        return 1
    return 0


async def invalid(message, server):
    await message.channel.send('Invalid request. Please refer to `m!help` for aid.')


async def check_votes(channel, server):
    for player in server.players.values():
        if player.alive and player.vote == None:
            return 0
    return 1  # everyone alive has voted


async def daytime(channel, server):
    if server.settings['daystart']:
        server.round += 1

    if not (server.settings['daystart'] and server.round == 1):  # night actions were taken
        server.saves = []
        for player in server.players.values():
            if player.alive and player.role == 'normalcop':  # normal cop report
                user = await openai.fetch_user(player.id)
                if player.cur_choice is None:
                    await user.send('You inquired about nobody, and so you receive no report.')
                else:
                    target = await openai.fetch_user(player.cur_choice.id)
                    await user.send('You received a report that **%s** is %s.' % (
                        target.name, ['innocent', 'guilty'][player.cur_choice.role == 'mafia']))
            elif player.alive and player.role == 'paritycop':  # parity cop report
                user = await openai.fetch_user(player.id)
                if player.cur_choice == None:
                    await user.send('You inquired about nobody, and so you receive no report.')
                elif player.lst_choice == None:
                    target = await openai.fetch_user(player.cur_choice.id)
                    await user.send(
                        'Your next target will be compared to **%s**, and you will determine whether their alignments are the same or not.' % target.name)
                else:
                    lst = await openai.fetch_user(player.lst_choice.id)
                    cur = await openai.fetch_user(player.cur_choice.id)
                    if [player.lst_choice.role, player.cur_choice.role].count(
                            'mafia') == 1 or player.lst_choice.role != player.cur_choice.role:
                        await user.send('You received a report that **%s** and **%s** are of different alignments.' % (
                            lst.name, cur.name))
                    else:
                        await user.send('You received a report that **%s** and **%s** are of the same alignment.' % (
                            lst.name, cur.name))
            elif player.alive and player.role == 'doctor' and player.action:  # doctor save
                server.saves.append(player.cur_choice)

        # mafia kill

        tars = [player.cur_choice for player in server.players.values() if (player.alive and player.role == 'mafia')]
        kill = None
        for tar in tars:
            if tars.count(tar) > len(tars) / 2:
                kill = tar

        if kill != None and kill != 'no-kill' and kill not in server.saves:
            await channel.send('<@%s> has been killed in the night!' % str(kill.id))
            await death(channel, kill.id, server)
            #TODO Insert in predictorAI knowledge that player has been killed. 
            server.predictorAI.deaths.append((server.round, server.players[kill.id])) # (Round, Player Object)
            server.predictorAI.world_facts.append((server.round, 'Player %s has been killed.' % kill.id))
            server.predictorAI.players.pop(kill.id) 

            if await check_end(channel, server):
                return
        else:
            await channel.send('It was a quiet night, without any deaths.')
            await channel.send(m_predict(server.predictorAI))
            # Make a prediction here. Maybe something along the lines of 'predictorAI predicts that the mafia is X.'

    await channel.send(
        'It is day %d! You have %s minutes to decide upon a lynch.' % (server.round, str(server.settings['limit1'])))

    server.phase = 1
    server.time = server.settings['limit1']
    if server.time != 'inf':
        server.time *= 60  # put time in seconds

    start_time = time.time()

    for player in server.players.values():  # reset all players' votes
        player.vote = None

    while (server.settings['limit1'] == 'inf' or (time.time() - start_time) < server.settings[
        'limit1'] * 60) and server.running:
        if server.time != 'inf':
            server.time = server.settings['limit1'] * 60 - (time.time() - start_time)
        if await check_votes(channel, server):
            break
        await asyncio.sleep(1)

    if not server.running:
        return

    votes = [player.vote for player in server.players.values() if player.alive]
    lynch = None
    for vote in votes:
        if votes.count(vote) > len(votes) / 2:
            lynch = vote

    if lynch == None or lynch == openai.user.id:
        await channel.send('The townspeople have decided to lynch nobody.')

        #TODO Make an update to world facts. 
        server.predictorAI.world_facts.append((server.round, 'The townspeople have decided to lynch nobody on round {}.'.format(server.round)))
    else:
        await channel.send('The townspeople have lynched <@%s>.' % str(lynch))
        #TODO Update predictorAI.deaths and update world facts
        server.predictorAI.deaths.append((server.round, server.players[lynch])) # (Round, Player Object)
        server.predictorAI.world_facts.append((server.round, 'The townspeople have lynched <@%s>' % str(lynch)))

        await death(channel, lynch, server)
        if await check_end(channel, server):
            return
    await nighttime(channel, server)


options_text = {
    'normalcop': 'Please select a player to investigate, by sending the number corresponding to your choice.',
    'paritycop': 'Please select a player to investigate, by sending the number corresponding to your choice.',
    'doctor': 'Please select a player to save, by sending the number corresponding to your choice:'
}


async def get_options(player, server):
    player.options = []
    for p in server.players.values():
        if p == player and not (
                player.role == 'doctor' and server.settings['selfsave']) and not player.role == 'paritycop':
            continue
        if player.role == 'paritycop' and p == player.lst_choice:
            continue
        if player.role == 'doctor' and p == player.lst_choice:
            continue
        user = await openai.fetch_user(p.id)
        player.options.append([len(player.options), user, p])


async def output_options(player, server):
    user = await openai.fetch_user(player.id)
    await user.send(options_text[player.role])
    await user.send('\n'.join(['%d - **%s**' % (option[0], option[1].name) for option in player.options]))


async def maf_options(mafias, server):
    options = [[0, openai.user, 'no-kill']]
    for player in server.players.values():
        if player.alive and player.role != 'mafia':
            options.append([len(options), await openai.fetch_user(player.id), player])
    for player in mafias:
        player.options = options
        user = await openai.fetch_user(player.id)
        if len(mafias) > 1:
            await user.send('The other remaining mafia are:\n' + '\n'.join(
                ['**%s**' % (await openai.fetch_user(mafia.id)).name for mafia in mafias if mafia != player]))
            await user.send(
                'You will be notified of their votes regarding whom to kill. If a majority is not reached by daytime, nobody will be targeted.')
        else:
            await user.send('You are the only remaining mafia.')
        await user.send(
            'Please select a player to kill, by sending the corresponding number. Selecting this bot will represent the choice to no-kill.')
        await user.send('\n'.join(['%d - **%s**' % (option[0], option[1].name) for option in player.options]))


async def m_ncop(player, server, choice):
    user = await openai.fetch_user(player.id)
    target = player.options[choice][1].name
    await user.send(
        'You have selected **%s** as the target of your investigation. You will recieve a report in the morning.' % target)
    await user.send('You may change your choice as long as not everyone has completed their night action.')


async def m_pcop(player, server, choice):
    user = await openai.fetch_user(player.id)
    target = player.options[choice][1].name
    if not player.lst_choice:
        await user.send(
            'You have selected **%s** as the target of your investigation. Remember that you will not recieve a report in the morning, as you are a parity cop.' % target)
    else:
        lst = await openai.fetch_user(player.lst_choice.id)
        await user.send(
            'You have selected **%s** as the target of your investigation, to be compared to **%s**. You will recieve a report in the morning.' % (
                target, lst.name))
    await user.send('You may change your choice as long as not everyone has completed their night action.')


async def m_doc(player, server, choice):
    user = await openai.fetch_user(player.id)
    target = player.options[choice][1].name
    await user.send(
        'You have selected **%s** as the target of your save. They will be immune to death tonight.' % target)
    await user.send('You may change your choice as long as not everyone has completed their night action.')


async def m_maf(player, server, choice):
    user = await openai.fetch_user(player.id)
    target = player.options[choice][1].name
    await user.send('You have selected **%s** as your target to kill.' % target)

    tars = [player.cur_choice for player in server.players.values() if (player.alive and player.role == 'mafia')]
    maj = None
    for tar in tars:
        if tars.count(tar) > len(tars) / 2:
            maj = tar

    if maj == None:
        await user.send('There is presently no majority in your votes.')
    elif maj == 'no-kill':
        await user.send('There is presently a majority vote to no-kill.')
    else:
        await user.send(
            'There is presently a majority vote to kill **%s**.' % (await openai.fetch_user(maj.id)).name)

    for p in server.players.values():
        if p == player or p.role != 'mafia' or not p.alive:
            continue
        maf_user = await openai.fetch_user(p.id)
        await maf_user.send('**%s** has selected **%s** as their target to kill.' % (user.name, target))
        if maj == None:
            await user.send('There is presently no majority in your votes.')
        elif maj == 'no-kill':
            await user.send('There is presently a majority vote to no-kill.')
        else:
            await user.send(
                'There is presently a majority vote to kill **%s**.' % (await openai.fetch_user(maj.id)).name)


pr_funcs = {
    'normalcop': m_ncop,
    'paritycop': m_pcop,
    'doctor': m_doc,
    'mafia': m_maf
}


async def check_action(player, server, message):
    query = message.content.split()
    try:
        choice = int(query[0])
        if choice < 0 or choice >= len(player.options):
            await message.channel.send('Please input a valid option.')
            return
        player.cur_choice = player.options[choice][2]
        if not player.action:
            player.action = 1
            server.actions -= 1
        func = pr_funcs[player.role]
        await func(player, server, choice)
    except:
        await message.channel.send('Please input a valid option.')


async def nighttime(channel, server):
    if not server.settings['daystart']:
        server.round += 1

    await channel.send('It is now night %d. If you have a nighttime action, you have %s minutes to take it.' % (
        server.round, str(server.settings['limit2'])))

    server.phase = 0
    server.time = server.settings['limit2']
    if server.time != 'inf':
        server.time *= 60  # put time in seconds
    server.actions = sum([player.alive and player.role in power_roles for player in server.players.values()])
    server.saves = []

    mafias = []

    for player in server.players.values():
        if player.role == 'mafia':
            player.action = 0
            mafias.append(player)
        elif player.role in power_roles:
            player.action = 0
            if player.cur_choice:
                player.lst_choice = player.cur_choice
            await get_options(player, server)
            await output_options(player, server)

    await maf_options(mafias, server)

    start_time = time.time()
    while (server.settings['limit2'] == 'inf' or (time.time() - start_time) < server.settings[
        'limit2'] * 60) and server.running and server.actions:
        if server.time != 'inf':
            server.time = server.settings['limit2'] * 60 - (time.time() - start_time)
        await asyncio.sleep(1)

    await daytime(channel, server)


async def m_help(message, author, server):
    query = message.content.split()
    if len(query) == 1:
        await message.channel.send('\n'.join(help_text))
    elif len(query) == 2 and query[1] in commands:
        await message.channel.send(commands[query[1]])
    else:
        await invalid(message)


async def m_h2p(message, author, server):
    await message.channel.send('\n'.join(h2p_text))


async def m_start(message, author, server):
    if server.running:
        await message.channel.send('The game is already ongoing.')
        return

    '''
    if sum([val for val in server.setup.values()]) != sum([player.ingame for player in server.players.values()]):
        await message.channel.send('The number of roles does not match the number of players!')
        return
    if sum([val for val in server.setup.values()]) / 2 <= server.setup['mafia']:
        await message.channel.send('The setup is invalid. Mafia cannot start with half of or more than half of the total number of players.')
        return
    if server.setup['mafia'] == 0:
        await message.channel.send('The setup is invalid. There must be at least one mafia in the game.')
        return
    '''

    # distribution of roles
    allRoles = []
    for key in server.setup:
        allRoles = allRoles + [key] * server.setup[key]

    random.shuffle(allRoles)

    for player in server.players.values():
        role = allRoles.pop()
        player.role = role
        user = await openai.fetch_user(player.id)
        await user.send('Your role is `%s`.' % role)

    # resetting player variables
    for player in server.players.values():
        player.cur_choice = None
        player.lst_choice = None
        player.vote = None
        player.alive = 1

    server.running = 1
    server.round = 0

    # TODO
    # Initialize the predictorAI object with the current players.
    predictor = PredictorAI(server.players)
    server.predictorAI = predictor
    print("PredictorAI players:", predictor.players)

    await message.channel.send('The game has begun!')
    if server.settings['daystart']:
        await daytime(message.channel, server)
    else:
        await nighttime(message.channel, server)


async def m_end(message, author, server):  # can only end game if currently playing (alive) or server mod/admin
    if not server.running:
        await message.channel.send('There is no ongoing game to end.')
        return
    if message.author.guild_permissions.administrator or (author in server.players and server.players[author].alive):
        await game_end(message.channel, 'None', server)
    else:
        await message.channel.send('You do not have permission to end the game!')


async def m_roles(message, author, server):
    await message.channel.send('\n'.join(roles_text))


async def m_set(message, author, server):
    if server.running:
        await message.channel.send('Game is ongoing.')
        return
    query = message.content.split()
    if query[1] not in server.setup or len(query) < 3:
        await invalid(message)
        return
    try:
        num = float(query[2])
    except ValueError:
        await invalid(message)
        return
    if num != int(num):
        await message.channel.send('Invalid input: inputted quantity must be integer.')
    elif num < 0:
        await message.channel.send('Invalid input: inputted quantity cannot be negative.')
    else:
        num = int(num)
        server.setup[query[1]] = num
        await message.channel.send('Successfully changed the number of `%ss` in the setup to `%d`.' % (query[1], num))


async def m_setup(message, author, server):
    if not sum([val for val in server.setup.values()]):
        await message.channel.send(
            'There are currently no roles in the setup. Use `m!set [role] [number]` to add some!')
        return
    await message.channel.send('\n'.join(
        ['The setup consists of:'] + [key + ': ' + str(server.setup[key]) for key in server.setup if
                                      server.setup[key]]))


async def m_settings(message, author, server):
    msg = ['%s : %d - %s' % (key, server.settings[key], toggle_text[server.settings[key]][key]) for key in
           toggle_text[0]]
    msg += ['Time limit for %s is %s minute(s).' % (['days', 'nights'][x - 1], server.settings['limit' + str(x)]) for x
            in [1, 2]]
    await message.channel.send('\n'.join(msg))


async def m_toggle(message, author, server):
    if server.running:
        await message.channel.send('Game is ongoing.')
        return
    query = message.content.split()
    if query[1] in server.settings:
        server.settings[query[1]] ^= 1
        await message.channel.send(toggle_text[server.settings[query[1]]][query[1]])
    else:
        await invalid(message)


async def m_setlimit(message, author, server):
    if server.running:
        await message.channel.send('Game is ongoing.')
        return
    query = message.content.split()
    if query[2] == 'inf':
        if query[1] == 'day':
            server.settings['limit1'] = 'inf'
            await message.channel.send('Time limit for day set to infinite minutes.')
        else:
            server.settings['limit2'] = 'inf'
            await message.channel.send('Time limit for night set to infinite minutes.')
    else:
        try:
            lim = float(query[2])
            if lim < 1:  # time limit must be at least 1 minute
                await invalid(message)
                return
            if query[1] == 'day':
                server.settings['limit1'] = lim
                await message.channel.send('Time limit for day set to ' + query[2] + ' minutes.')
            else:
                server.settings['limit2'] = lim
                await message.channel.send('Time limit for night set to ' + query[2] + ' minutes.')
        except ValueError:
            await invalid(message)


async def m_join(message, author, server):
    if server.running:
        await message.channel.send('Game is ongoing: please wait until it ends before joining.')
        return
    if author in server.players:
        await message.channel.send('<@%s>, you are already in the game!' % str(author))
    elif author in allPlayers:
        await message.channel.send('<@%s>, you cannot be in more than one game at a time!' % str(author))
    else:
        allPlayers[author] = message.guild
        server.players[author] = Player(author, server)
        # TODO 
        # server.predictorAI.characters[author] = Player(author, server) # Maybe not the best idea because it contains the entire player's object.
        # server.predictorAI.current_players.append(author)
        # print("Author:", author)

        role = discord.utils.get(message.guild.roles, name='Mafia')
        await message.author.add_roles(role)
        await message.channel.send('<@%s> has joined the game.' % str(author))


async def m_leave(message, author, server):
    if author not in allPlayers or allPlayers[author] != message.guild:  # not server they're playing in
        await message.channel.send('<@%s>, you are not currently part of the game in this server.' % str(author))
        return
    if server.running and author in server.players:
        await message.channel.send('<@%s> has elected to leave the game.' % str(author))
        if server.players[author].alive:
            server.players[author].alive = 0
            server.players[author].ingame = 0
            if server.settings['continue']:
                await death(message.channel, author, server)
                if not server.phase and server.players[author].role in power_roles and not server.players[
                    author].action:  # if nighttime and power role unfulfilled
                    server.actions -= 1
                await check_end(message.channel, server)
            else:
                await game_end(message.channel, 'None', server)
        else:
            server.players[author].ingame = 0
            allPlayers.pop(author)  # allows player to join game in different server
            role = discord.utils.get(message.guild.roles, name='Mafia')
            message.author.remove_roles(role)
        return
    server.players.pop(author)

    #TODO Remove from predictorAI object as well.
    server.predictorAI.players.pop(author)

    allPlayers.pop(author)
    await message.channel.send('<@%s> has left the game.' % str(author))


async def m_vote(message, author, server):
    if not server.running:
        await message.channel.send('The game has not yet started. Don\'t be so hasty to vote!')
        return
    if author not in server.players or not server.players[
        author].alive or not server.phase:  # not playing, not alive, night
        await message.channel.send('You cannot vote!')
        return
    query = message.content.split()
    tar = query[1]
    try:
        if len(tar) <= 3 or tar[:2] != '<@' or tar[-1] != '>' or (
                int(tar[2:-1]) != openai.user.id and int(tar[2:-1]) not in server.players) or (
                int(tar[2:-1]) in server.players and not server.players[int(tar[2:-1])].alive):
            await message.channel.send(
                'That is an invalid voting target. Vote in the form `m!vote @user`, where user is a living player.')
            return
    except ValueError:
        await message.channel.send('That is an invalid voting target. Vote in the form `m!vote @user`.')
        return
    await message.channel.send('<@%s> has placed their vote on <@%s>.' % (str(author), str(tar[2:-1])))
    server.players[author].vote = int(tar[2:-1])


async def m_unvote(message, author, server):
    if not server.running:
        await message.channel.send('The game has not yet started. There\'s nobody to unvote!')
        return
    if author not in server.players or not server.players[
        author].alive or not server.phase:  # not playing, not alive, night
        await message.channel.send('You cannot change your vote at this time.')
        return
    server.players[author].vote = None
    await message.channel.send('<@%s> has removed their vote, and is now voting nobody.' % str(author))


async def m_status(message, author, server):
    if not server.running:
        await message.channel.send('The game has not yet started. There are no votes in effect.')
        return
    if author not in server.players or not server.players[
        author].alive or not server.phase:  # not playing, not alive, night
        await message.channel.send('Daytime is not in session. There are no votes in effect.')
        return
    num = sum([player.alive for player in server.players.values()])
    msg = ['The votes are currently as follows:']

    count = {}
    for player in server.players.values():
        if not player.alive:
            continue
        if player.vote == openai.user.id:
            msg.append('<@%s> is currently voting for a no-lynch.' % str(player.id))
        elif player.vote == None:
            msg.append('<@%s> is currently voting for nobody.' % str(player.id))
        else:
            msg.append('<@%s> is currently voting <@%s>' % (str(player.id), player.vote))
            if player.vote not in count:
                count[player.vote] = 1
            else:
                count[player.vote] += 1

    count2 = {}
    for i in range(num + 1):
        count2[i] = []

    for key in count:
        count2[count[key]].append(key)

    msg.append('Voting summary:')
    for i in range(num, -1, -1):
        if count2[i]:
            msg.append(str(i) + ' vote(s) on: ' + ', '.join(['<@%s>' % str(key) for key in count2[i]]))

    msg.append('No lynch: %d vote(s)' % sum(
        [player.vote == openai.user.id for player in server.players.values() if player.alive]))
    msg.append('Nobody: %d vote(s)' % sum([player.vote == None for player in server.players.values() if player.alive]))
    await message.channel.send('\n'.join([line for line in msg]))


async def m_players(message, author, server):
    num = sum([player.alive for player in server.players.values()])
    if not server.running:
        if not num:
            await message.channel.send('There are currently no players in the game. Type `m!join` to join!')
        else:
            await message.channel.send(
                ' '.join(['The following players are in the game:'] + ['<@%s>' % str(key) for key in server.players]))
        return
    await message.channel.send(' '.join(
        ['The following players are alive:'] + ['<@%s>' % str(player.id) for player in server.players.values() if
                                                player.alive]))


async def m_alive(message, author, server):
    if not server.running:
        await message.channel.send('There is no ongoing game. Use `m!setup` to see the current setup of the game.')
        return
    if not server.settings['reveal']:
        await message.channel.send('Remaining roles are unknown, due to the `reveal` setting being toggled off.')
    else:
        msg = ['Remaining roles are as follows:']
        msg += ['`%s` : %d' % (role, sum([player.role == role for player in server.players.values() if player.alive]))
                for role in server.setup]
        await message.channel.send('\n'.join(msg))


async def m_dead(message, author, server):
    if not server.running:
        await message.channel.send('There is no ongoing game. Use `m!players` to check who\'s planning to play.')
        return
    if not sum([player.alive == 0 for player in server.players.values()]):
        await message.channel.send('The graveyard is currently empty. Not for long, though...')
        return
    if not server.settings['reveal']:
        await message.channel.send(' '.join(
            ["The graveyard consists of:"] + ['<@%s>' % str(player.id) for player in server.players.values() if
                                              not player.alive]))
    else:
        await message.channel.send('\n'.join(
            ['The graveyard consists of:'] + ['<@%s>, who was a %s' % (str(player.id), player.role) for player in
                                              server.players.values() if not player.alive()]))


async def m_time(message, author, server):
    if not server.running:
        await message.channel.send('There is no ongoing game.')
        return
    if server.phase:
        if server.settings['limit1'] == 'inf':
            await message.channel.send('There is no time limit for daytime.')
        else:
            await message.channel.send('There are %d minutes and %d seconds remaining in the day.' % (
                int(server.time) / 60, int(server.time) % 60))
    else:
        if server.settings['limit2'] == 'inf':
            await message.channel.send('There is no time limit for nighttime.')
        else:
            await message.channel.send('There are %d minutes and %d seconds remaining in the night.' % (
                int(server.time) / 60, int(server.time) % 60))

async def m_predict(message, author, server):

    if not server.running:
        await message.channel.send('There is no ongoing game. Please start a game first.')
        # print("out here")
        return
    else:
        # print("In here")
        if not server.predictorAI:
            return
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are an analyzer who predicts who the current mafia player is. You have access to the following information: {server.predictorAI.world_facts}, which tells you what happened after every round. The current players in the game are: {server.predictorAI.players}. Make a strong prediction on who the mafia player is and explain logically how you came to this conclusion. If any of the variables are missing, please make a prediction based on the information you have. Predict the player id of the mafia player."
                    }
                ],
                temperature=1,
                max_tokens=256,
                top_p=1
            )
            result = response.choices[0].message.content
            print("predictorAI response:", result)
            await message.channel.send("Here we go again:", result)
            await message.channel.send(result)
            # await messages.channel.send(joke)
        except Exception as e:
            print(e)  # For debugging
            # return "Sorry, I can't make a prediction right now. Please try again later."
            await message.channel.send("Sorry, I can't make a prediction right now. Please try again later.")


async def m_testState(message, author, server):

    if not server.running:
        await message.channel.send('There is no ongoing game. Please start a game first.')
        return
    # Test the predictorAI object
    await message.channel.send("Testing the predictorAI object.")
    print("PredictorAI players:", server.predictorAI.players)
    print("PredictorAI deaths:", server.predictorAI.deaths)
    print("PredictorAI world facts:", server.predictorAI.world_facts)

async def m_test1(message, author, server):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are an analyzer who predicts who the current mafia player is. You have access to the following information: ['no one died round 1', 'p1 died last night'], which tells you what happened after every round. The current players in the game are: ['p1', 'p2', 'p3']. Make a strong prediction on who the mafia player is and explain logically how you came to this conclusion. If any of the variables are missing, please make a prediction based on the information you have. Predict the player id of the mafia player."
                }
            ],
            temperature=1,
            max_tokens=256,
            top_p=1
        )
        result = response.choices[0].message.content
        print("predictorAI response:", result)
        # await message.channel.send("Here we go again:", result)
        await message.channel.send(result)
        # await messages.channel.send(joke)
    except Exception as e:
        print(e)  # For debugging
        # return "Sorry, I can't make a prediction right now. Please try again later."
        await message.channel.send("Sorry, I can't make a prediction right now. Please try again later.")

to_func = {
    'help': m_help,  # DM
    'h2p': m_h2p,  # DM
    'start': m_start,
    'end': m_end,
    'roles': m_roles,  # DM
    'set': m_set,
    'setup': m_setup,
    'settings': m_settings,
    'toggle': m_toggle,
    'setlimit': m_setlimit,
    'join': m_join,
    'leave': m_leave,
    'vote': m_vote,
    'unvote': m_unvote,
    'status': m_status,
    'players': m_players,
    'alive': m_alive,
    'dead': m_dead,
    'time': m_time,
    'testPredict': m_predict,
    'testState': m_testState,
    'test1': m_test1
}

dm_funcs = [
    'help',
    'h2p',
    'roles'
]


@openai.event
async def on_message(message):
    # print('Message received: ' + message.content)
    print(f'{message.author}: {message.content}')
    # print("dir of message:", dir(message))
    # print("author & id of message:", message.author, message.id)
    # await message.channel.send('Received a message in this thread!')
    # print("message channel:", message.channel) # General: private
    # print(message.channel.type) # gen

    if message.guild not in servers:
        servers[message.guild] = Server()

    if message.channel.type == discord.ChannelType.private and message.author.id in allPlayers:
        # print('in allPlayers')
        server = servers[allPlayers[message.author.id]]
        player = server.players[message.author.id]
        if server.running and not server.phase and player.alive and player.role in power_roles:
            await check_action(player, server, message)

    if message.author == openai.user or len(message.content) < 2 or message.content[:2] != 'm!':
        return

    query = message.content[2:].split()

    # TODO: remove below
    # just for testing gpt connection
    if message.content.startswith('m!testgpt!'):
        word = message.content.split('m!testgpt!', 1)[1]  # Extract the word
        # print("word:", word)
        if word:  # If there's a word provided, generate and send back a joke
            await test_gpt_joke(message, word)
        else:
            await message.channel.send("Please provide a word for me to joke about. Use the format m!testgpt!{word}")
        return
    # TODO: remove above

    if len(query) and query[0] in commands:
        # print('Command received: ' + query[0])
        if message.channel.type == discord.ChannelType.private and query[0] not in dm_funcs:
            await message.channel.send('This function cannot be used in DMs.')
        else:
            # print('to_func: ' + query[0])
            func = to_func[query[0]]
            await func(message, message.author.id, servers[message.guild])
    else:
        await invalid(message, servers[message.guild])



openai.run(DISCORD_BOT_TOKEN)

'''
REMEMBER TO REMOVE TOKEN WHEN COMMITTING


Possible bugs or to-do:
- make sure nobody has mafia role upon joining a server (is this necessary?)
- does the text channel even have to be locked? consider having only private VC


REMINDERS:
- message.author.id (author) is integer, not string


NOTES:
- REMEMBER TO DISTINGUISH BETWEEN COMMANDS YOU CAN USE IN DM AND COMMANDS YOU CAN'T

GAMEPLAY:

All players are initially in both a text channel and a voice chat, and upon gamestart will be DM'd a role by the bot.

Mafia members will be DM'd by the bot, notifying them of the other mafia members, and will update on other mafias' votes.
 - There will be no direct communication between mafia (because bot cannot be in groupchat)

Doctor and cop will receive a prompt by the bot each night phase
 - Bot will list all living players (because you can't ping people not in the DM), and will prompt input of single integer
    - MAYBE USE THIS MECHANIC FOR NORMAL VOTING? TO AVOID PINGING OTHER PLAYERS
 - Normal cop cannot investigate himself, parity cop can, doctor can save himself if selfsave = 1, mafia cannot selfkill

Daytime discussion should primarily occur in VC, but players can use text channels if they want. Text channel will be used for voting and other in-game commands.

SHOULD VOTING END WHEN EVERYONE VOTES? OR WHEN A MAJORITY EXISTS? (latter is epicmafia.com format)


Nighttime will occur in DMs. The main text channel will be locked and nobody will be able to speak there (might need to end game? rethink this).
Graveyard text channel will be able to continue to talk.


'''
