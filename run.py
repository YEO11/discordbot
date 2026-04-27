import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks
import datetime
import os
import requests
from discord.ui import View, Select, Button
import asyncio

API_KEY = 'AIzaSyDN9uGo32uuTxAR2Upw4xalVw4mciPmYkU'
API_URL = f'https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={API_KEY}'

'''
- 수업 등록한 사람들한테만 보이는 메세지
- 수업 자동 등록 기능
- 학생 이름 기준으로 강의, 반 추가
- 'Roles': 이름, 파이썬 오전반, 등등등
- 출결 관리
- 학생, 강사 기능 구분 
- 강의 시작, 끝, 쉬는 시간 타이머
- 백준, 프로그래머스 푼 문제 개수 출력
- 강퇴, 경고 부여
- 지각시 멘션
'''

lecture = {}
lecture_attendance = {}
students = {}  
teachers = {}
warning_stack = {}
classes = {}
now = datetime.datetime.now()

teachers["Teacher1"] = '철수쌤'
teachers["Teacher2"] = '영희쌤'
teachers["Teacher3"] = '민수쌤'

students["student1"] = "홍길동"
students["student2"] = "김철수"
students["student3"] = "이영희"
students['rlawhtpq'] = '백승열'

load_dotenv()

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/')

def censorship(text_to_analyze):
    data = {
        "comment": {"text": text_to_analyze},
        "languages": ["ko"],
        "requestedAttributes": {"TOXICITY": {}},
    }
    response = requests.post(API_URL, json=data)
    if response.status_code == 200:
        result = response.json()
        return result["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
    else:
        print(f"Error: API 요청 실패 (상태 코드 {response.status_code})")
        return 0

@bot.event
async def on_ready():
    print(f'{bot.user} 디스코드 준비 완료!')
    print('-'*35)

@tasks.loop(seconds=1)  
async def send_class_reminders():
    guild = bot.get_guild(1324237420798939156)
    print('수업 시간 체크')

    for username, lectures in lecture.items():
        # 학생마다 수업 목록 확인
        for time_obj, teacher in lectures:
            # 수업 시간이 10분 이내로 다가온 경우
            if now + datetime.timedelta(minutes=10) > time_obj > now:
                member = guild.get_member_named(username)
                if member:
                    formatted_time = time_obj.strftime("%Y년 %m월 %d일 %H시 %M분")
                    await guild.text_channels[0].send(f"{member.mention}님, {teacher}의 수업이 {formatted_time}에 시작됩니다. 준비하세요!")

# @bot.event
# async def on_message(ctx: discord.Interaction, message):
#     username = message.author.name
#     guild = message.guild
#     member = guild.get_member_named(message.author)
#     # 봇 자신이 보낸 메시지는 무시
#     if message.author == bot.user:
#         return

#     print(f"채팅 감지: {message.author}: {message.content}")

#     # 욕설 감지
#     toxic_score = int(censorship(message.content) * 100)
#     if toxic_score >= 50:
#         await message.delete()
#         await message.channel.send(
#             f"{username}님, 부적절한 표현이 감지되었습니다. ({toxic_score}% 부적절)"
#         )

#     # 명령어와 충돌 방지
#     await bot.process_commands(message)

# /학생등록
@bot.slash_command(name="학생등록", description="student register")
async def student_register(ctx: discord.Interaction, username: str, nickname: str):
    guild = ctx.guild
    member = guild.get_member_named(username)
    
    if not member:
        await ctx.response.send_message("이 유저는 서버에 존재하지 않습니다.")
        return

    if username not in students:
        await ctx.response.send_message("아직 학생 등록을 안하셨습니다.")

        yes_button = discord.ui.Button(label="Yes", custom_id="yes", style=discord.ButtonStyle.success)
        no_button = discord.ui.Button(label="No", custom_id="no", style=discord.ButtonStyle.danger)

        async def button_callback(interaction: discord.Interaction):
            if interaction.data['custom_id'] == 'yes':
                students[username] = nickname
                student_role = discord.utils.get(guild.roles, name="학생")
                if not student_role:
                    student_role = await guild.create_role(name="학생")
   
                if student_role:
                    await member.add_roles(student_role)
   
                await interaction.response.send_message(f"{username}님을 성공적으로 학생으로 등록하였습니다!")
            elif interaction.data['custom_id'] == 'no':
                await interaction.response.send_message("취소 되었습니다.")

            await interaction.message.edit(view=None)

        yes_button.callback = button_callback
        no_button.callback = button_callback

        view = discord.ui.View()
        view.add_item(yes_button)
        view.add_item(no_button)

        await ctx.send(f"학생을 등록하시겠습니까?\n아이디: {username} 별명: {nickname}", view=view)
    else:
        await ctx.response.send_message(f"{username}님은 이미 계정이 등록되어 있습니다.")

# /강사등록
@bot.slash_command(name="강사등록", description="teacher register")
async def teacher_register(ctx: discord.Interaction, username: str, nickname: str):  
    guild = ctx.guild
    member = guild.get_member_named(username)

    if not member:
        await ctx.response.send_message("이 유저는 서버에 존재하지 않습니다.")

    elif username not in students:
        await ctx.response.send_message("아직 강사를 등록을 안하셨습니다.")

        yes_button = discord.ui.Button(label="Yes", custom_id="yes", style=discord.ButtonStyle.success)
        no_button = discord.ui.Button(label="No", custom_id="no", style=discord.ButtonStyle.danger)

        async def button_callback(interaction: discord.Interaction):
            if interaction.data['custom_id'] == 'yes':
                teachers[username] = nickname
                teacher_role = discord.utils.get(guild.roles, name="강사")
                if not teacher_role:
                    teacher_role = await guild.create_role(name="강사")
                if teacher_role:
                    await member.add_roles(teacher_role)
                await interaction.response.send_message(f"{username}님을 성공적으로 강사로 등록하였습니다!")
            elif interaction.data['custom_id'] == 'no':
                await interaction.response.send_message("취소 되었습니다.")

            await interaction.message.edit(view=None)

        yes_button.callback = button_callback
        no_button.callback = button_callback

        view = discord.ui.View()
        view.add_item(yes_button)
        view.add_item(no_button) 
        
        await ctx.send("강사를 등록하시겠습니까?", view=view)
    else:
        await ctx.response.send_message(f"{username}님은 이미 계정이 등록되어 있습니다.")

# /수업등록
@bot.slash_command(name="수업등록", description="lecture register (YYYY-MM-DD HH:MM)")
async def register_class(ctx: discord.Interaction, date: str, time: str):
    username = ctx.author.name

    # 수업 시간을 파싱
    time_obj = datetime.datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M")
    if now > time_obj:
        await ctx.response.send_message('이미 지난 날짜입니다.')

    # 서버의 모든 학생들 목록 가져오기
    student_options = [discord.SelectOption(label=name, value=student) for student, name in students.items()]
    if not student_options:
        await ctx.response.send_message("등록된 학생이 없습니다.")

    # 학생 선택 메뉴 생성 (다중 선택 가능)
    student_select_menu = Select(
        placeholder="학생을 선택하세요",
        options=student_options,
        min_values=1,  # 최소 1명 선택
        max_values=len(student_options),  # 최대 학생 수
    )

    async def student_select_callback(interaction: discord.Interaction):
        selected_students = student_select_menu.values

        # 선생님 선택 메뉴 생성
        teacher_options = [discord.SelectOption(label=name, value=teacher) for teacher, name in teachers.items()]
        teacher_select_menu = Select(
            placeholder="강사를 선택하세요",
            options=teacher_options,
            min_values=1,
            max_values=1,
        )

        async def teacher_select_callback(inner_interaction: discord.Interaction):
            selected_teacher = teacher_select_menu.values[0]

            # 수업 등록 처리
            for student in selected_students:
                if student not in lecture:
                    lecture[student] = [(time_obj, selected_teacher)]
                else:
                    lecture[student].append((time_obj, selected_teacher))

            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
            clock_obj = datetime.datetime.strptime(time, "%H:%M")
            formatted_date = date_obj.strftime("%Y년 %m월 %d일")
            formatted_clock = clock_obj.strftime("%H:%M")

            formatted_students = []
            for student in selected_students:
                formatted_students.append(students[student])

            await inner_interaction.response.send_message("수업이 등록되었습니다!")
            await ctx.send(f'강사: {teachers[selected_teacher]}\n학생: {", ".join(formatted_students)}\n날짜: {formatted_date}\n시간: {formatted_clock} ')

        teacher_select_menu.callback = teacher_select_callback
        teacher_view = View()
        teacher_view.add_item(teacher_select_menu)

        await interaction.response.send_message("강사를 선택하세요:", view=teacher_view)

    student_select_menu.callback = student_select_callback

    # 학생 선택 뷰 생성 및 전송
    student_view = View()
    student_view.add_item(student_select_menu)
    await ctx.response.send_message("학생을 선택하세요:", view=student_view)

# /출석
@bot.slash_command(name="출석", description="attendance check")
async def attendance(ctx: discord.Interaction):
    username = ctx.author.name

    # 학생이 등록되어 있는지 확인
    if username not in students:
        await ctx.response.send_message(f"{username}님은 등록된 학생이 아닙니다. 먼저 등록해주세요.")
        return

    # 해당 학생의 수업 정보 확인
    if username not in lecture or not lecture[username]:
        await ctx.response.send_message(f"{username}님은 등록된 수업이 없습니다.")
        return

    # 현재 시간 확인
    now = datetime.datetime.now()
    lecture[username].sort()  # 수업 시간을 오름차순 정렬
    next_lecture = lecture[username][0]  # 가장 가까운 수업 정보 가져오기
    time, teacher = next_lecture  # 수업 시간과 강사 정보 분리

    # 출결 기록 초기화
    if username not in lecture_attendance:
        lecture_attendance[username] = {'출석': 0, '결석': 0, '지각': 0}

    # 수업 시간과 현재 시간 비교
    if now >= time:
        if (now - time) >= datetime.timedelta(minutes=5):  # 5분 이상 지각
            await ctx.response.send_message(f"{username}님이 {teacher}의 수업에 지각하였습니다.")
            lecture_attendance[username]['지각'] += 1
        elif 0 <= (now - time) < datetime.timedelta(minutes=5):  # 정상 출석
            await ctx.response.send_message(f"{username}님이 {teacher}의 수업에 출석하였습니다!")
            lecture_attendance[username]['출석'] += 1
        lecture[username].pop(0)  # 출석 완료된 수업 제거
    else:
        # 수업 시작 전
        await ctx.response.send_message(f"아직 {teacher}의 수업이 시작하지 않았습니다.")

# /수업 목록
@bot.slash_command(name="수업목록", description="lecture list")
async def lecture_list(ctx: discord.Interaction, username):
    guild = ctx.guild
    member = guild.get_member_named(username)
    if not member:
        await ctx.response.send_message('서버에 존재하지 않는 학생입니다.')
    if username not in lecture:
        await ctx.response.send_message('등록된 수업이 없습니다.')
    else:
        user_lectures = []
        lecture[username].sort()
        cnt = 0
        for time_obj, teacher in lecture[username]:
            cnt += 1
            formatted_time = time_obj.strftime("%Y년 %m월 %d일 %H시 %M분")
            user_lectures.append(f'{cnt}) 교사 : {teachers[teacher]}, 수업 날짜 : {formatted_time}')

        await ctx.response.send_message(f'{username}님의 수업 목록 (총 {cnt}개)\n' + '\n'.join(user_lectures))

#/반등록
@bot.slash_command(name="반등록", description="class register")
async def register_class(ctx: discord.Interaction, class_name: str, day: str, time):
    username = ctx.author.name
    guild = ctx.guild
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    if day not in weekdays:
        await ctx.response.send_message("잘못된 요일입니다.")
    if class_name in classes:
        await ctx.response.send_message("같은 이름으로 등록된 반이 있습니다.")

    # 서버의 모든 학생들 목록 가져오기
    student_options = [discord.SelectOption(label=name, value=student) for student, name in students.items()]
    if not student_options:
        await ctx.response.send_message("등록된 학생이 없습니다.")

    # 학생 선택 메뉴 생성 (다중 선택 가능)
    student_select_menu = Select(
        placeholder="학생을 선택하세요",
        options=student_options,
        min_values=1,  # 최소 1명 선택
        max_values=len(student_options),  # 최대 학생 수
    )

    async def student_select_callback(interaction: discord.Interaction):
        selected_students = student_select_menu.values

        # 선생님 선택 메뉴 생성
        teacher_options = [discord.SelectOption(label=name, value=teacher) for teacher, name in teachers.items()]
        teacher_select_menu = Select(
            placeholder="강사를 선택하세요",
            options=teacher_options,
            min_values=1,
            max_values=1,
        )

        async def teacher_select_callback(inner_interaction: discord.Interaction):
            selected_teacher = teacher_select_menu.values[0]
            if class_name not in classes:
                classes[class_name] = [(selected_students, selected_teacher, day, time)]
            else:
                classes[student].append((selected_students, selected_teacher, day, time))

            # 수업 등록 처리
            for student in selected_students:
                member = guild.get_member_named(student)
                if member:
                    class_role = discord.utils.get(guild.roles, name=class_name)
                    if not class_role:
                        class_role = await guild.create_role(name=class_name)
                    await member.add_roles(class_role)
                
                      

            formatted_students = []
            for student in selected_students:
                formatted_students.append(students[student])

            await inner_interaction.response.send_message("반이 등록되었습니다!")
            await ctx.send(f'반 이름: {class_name}\n강사: {selected_teacher}\n학생: {", ".join(formatted_students)}\n요일: {day}\n시간: {time}')

        teacher_select_menu.callback = teacher_select_callback
        teacher_view = View()
        teacher_view.add_item(teacher_select_menu)

        await interaction.response.send_message("강사를 선택하세요:", view=teacher_view)

    student_select_menu.callback = student_select_callback

    # 학생 선택 뷰 생성 및 전송
    student_view = View()
    student_view.add_item(student_select_menu)
    await ctx.response.send_message("학생을 선택하세요:", view=student_view)

@bot.slash_command(name="스톱워치", description="stopwatch")
async def stopwatch(ctx: discord.Interaction, h: int, m: int, s: int):
    username = ctx.author.name
    if h + m + s == 0:
        await ctx.response.send_message('스톱워치의 최소시간은 1초입니다.')
        return

    total_seconds = 0
    time_to_seconds = {'M': 60, 'H': 3600}

    total_seconds += time_to_seconds['H'] * h
    total_seconds += time_to_seconds['M'] * m
    total_seconds += s

    while total_seconds:
        total_seconds -= 1
        await asyncio.sleep(1) 

    await ctx.response.send_message(f'{username}님의 타이머가 끝났습니다!')

token = ""
bot.run(token)
