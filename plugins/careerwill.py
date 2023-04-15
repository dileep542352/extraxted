from pyrogram import Client, filters 
from utils import get_datetime_str, create_html_file

import cloudscraper
import time
import os


@Client.on_message(
    filters.private
    & filters.command(['careerwill'])
)
async def classplus(client, message):

    def get_source_url(scrapper, api, class_id, video_id):

        params = {
            'base': 'web',
            'type': 'brightcove',
            'vid': class_id
        }

        res = scrapper.get(f'{api}/livestreamToken', params=params)

        if res.status_code == 200:
            res = res.json()

            brightcove_token = res['data']['token']

            brightcove_api = 'https://edge-auth.api.brightcove.com/playback/v1'
            brightcove_account_id = 6206459123001

            scrapper.headers['authorization'] = f'Bearer {brightcove_token}'

            res = scrapper.get(f'{brightcove_api}/accounts/{brightcove_account_id}/videos/{video_id}')

            scrapper.headers.pop('authorization')

            if res.status_code == 200:
                res = res.json()

                source = res['sources'][5]
                source_url = source['src']

                return source_url
            
            else:
                raise Exception('Failed to get source')
            
        else:
            raise Exception('Failed to get livestream token.')
        

    headers = {
        'origin': 'https://web.careerwill.com',
        'origintype': 'web',
        'referer': 'https://web.careerwill.com/',
    }

    api = 'https://elearn.crwilladmin.com/api/v3'

    try: 

        reply = await message.chat.ask(
            (
                '**'
                'Send your credentials as shown below.\n\n'
                'Phone Number | Email Id\n'
                'Password\n\n'
                'OR\n\n'
                'Access Token'
                '**'
            ),
            reply_to_message_id = message.id
        )
        creds = reply.text

        scrapper = cloudscraper.create_scraper()
        scrapper.headers.update(headers)

        logged_in = False

        if '\n' in creds:
            username, passowrd = [cred.strip() for cred in creds.split('\n')]

            if ('@' in username and '.' in username) or (username.isdigit() and len(username) == 10):

                data = {
                    'email': username,
                    'password': passowrd
                }

                res = scrapper.post(f'{api}/login-other', data=data)

                if res.status_code == 200:
                    res = res.json()

                    token = res['data']['token']

                    scrapper.headers['token'] = token

                    reply = await reply.reply(
                        (
                            '**'
                            'Your Access Token for future uses - \n\n'
                            '**'
                            '<pre>'
                            f'{token}'
                            '</pre>'
                        ),
                        quote=True
                    )

                    logged_in = True

                else:
                    raise Exception('Failed to login.')

            else:
                raise Exception('Failed to validate credentials.')
            
        else:

            token = creds.strip()
            scrapper.headers['token'] = token

            logged_in = True


        if logged_in:

            res = scrapper.get(f'{api}/my-batch')

            if res.status_code == 200:
                res = res.json()

                batches = res['data']['batchData']

                if batches:

                    text = ''

                    for cnt, batch in enumerate(batches):

                        name = batch['batchName']
                        instructor= batch['instructorName']

                        text += f'{cnt + 1}. {name} by {instructor}\n'

                    reply = await message.chat.ask(
                        (
                            '**'
                            'Send index number of the batch to download.\n\n'
                            f'{text}'
                            '**'
                        ),
                        reply_to_message_id = reply.id
                    )

                    if reply.text.isdigit() and len(reply.text) <= len(batches):

                        selected_batch_index = int(reply.text.strip())

                        batch = batches[selected_batch_index - 1]

                        selected_batch_id = batch['id']
                        selected_batch_name = batch['batchName']

                        params = {
                            'type': 'class'
                        }

                        res = scrapper.get(f'{api}/batch-topic/{selected_batch_id}', params=params)

                        if res.status_code == 200:
                            res = res.json()

                            topics = res['data']['batch_topic']

                            if topics:

                                text = ''

                                for cnt, topic in enumerate(topics):

                                    name = topic['topicName']

                                    text += f'{cnt + 1} - {name}\n'

                                reply = await message.chat.ask(
                                    (
                                        '**'
                                        'Send index number of the topic to download. '
                                        'You can also send a range (2-5) or "0" to download all.\n\n'
                                        f'{text}'
                                        '**'
                                    ),
                                    reply_to_message_id = reply.id
                                )

                                if '-' in reply.text:
                                    start, stop = [int(index.strip()) for index in reply.text.split('-')]
                                    
                                    if not (start >= 1 and stop <= len(topics) and start <= stop):
                                        start, stop = None, None
                                        
                                else:
                                    start = int(reply.text.strip())

                                    if start == 0:
                                        start, stop = 1, len(topics)

                                    elif start >= 1 and start <= len(topics):
                                        stop = start

                                    else:
                                        start, stop = None, None


                                if start and stop:

                                    batch_contents = []

                                    loader = await reply.reply(
                                        (
                                            '**'
                                            'Extracting batch...'
                                            '**'
                                        ),
                                        quote=True
                                    )

                                    prev_edit = 0
                                    prog = 5

                                    for topic in topics[start - 1:stop]:

                                        topic_id = topic['id']

                                        params = {
                                            'topicId': topic_id
                                        }

                                        res = scrapper.get(f'{api}/batch-detail/{selected_batch_id}', params=params)

                                        if res.status_code == 200:
                                            res = res.json()

                                            classes = res['data']['class_list']['classes']

                                            topic_contents = []

                                            for class_ in classes:

                                                name = class_['lessonName']
                                                ext = class_['lessonExt']
                                                video_id = class_['lessonUrl']

                                                url = None

                                                if ext == 'youtube':
                                                    url = f'https://www.youtube.com/watch?v={video_id}'

                                                elif ext == 'brightcove':
                                                    url = get_source_url(scrapper, api, class_['id'], video_id)

                                                if url:
                                                    topic_contents.append(f'{name}: {url}\n')

                                                else:
                                                    raise Exception('Unknown source extension.')
                                                
                                                if time.time() - prev_edit >= 3:

                                                    dots = '.' * prog

                                                    await loader.edit_text(
                                                        (
                                                            '**'
                                                            f'Extracting batch{dots}'
                                                            '**'
                                                        )
                                                    )

                                                    prog = 1 if prog == 5 else prog + 1
                                                    prev_edit = time.time()

                                                
                                            batch_contents += topic_contents
                                    
                                    await loader.delete()

                                    if batch_contents:

                                        caption = (
                                            '**'
                                            'App Name : Classplus\n'
                                            f'Batch Name : {selected_batch_name}'
                                            '**'
                                        )

                                        text_file = f'assets/{get_datetime_str()}.txt'
                                        open(text_file, 'w').writelines(batch_contents)

                                        await client.send_document(
                                            message.chat.id,
                                            text_file,
                                            caption=caption,
                                            file_name=f"{selected_batch_name}.txt",
                                            reply_to_message_id=reply.id
                                        )

                                        html_file = f'assets/{get_datetime_str()}.html'
                                        create_html_file(html_file, selected_batch_name, batch_contents)

                                        await client.send_document(
                                            message.chat.id,
                                            html_file,
                                            caption=caption,
                                            file_name=f"{selected_batch_name}.html",
                                            reply_to_message_id=reply.id
                                        )

                                        os.remove(text_file)
                                        os.remove(html_file)
                                    
                                    else:
                                        raise Exception('Did not found any content in batch.')

                                else:
                                    raise Exception('Failed to validate topic selection.')
                                
                            else:
                                raise Exception('Did not found any topic in batch.')
                            
                        else:
                            raise Exception('Failed to get batch topics.')
                        
                    else:
                        raise Exception('Failed to validate batch selection.')
                    
                else:
                    raise Exception('Did not found any batch.')
                
            else:
                raise Exception('Failed to get batches.')


    except Exception as error:

        print(f'Error : {error}')

        await reply.reply(
            (
                '**'
                f'Error : {error}'
                '**'
            ),
            quote=True
        )

