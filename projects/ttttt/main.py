import turtle

# Initialize the screen and set up the window size
screen = turtle.Screen()
screen.title("Pong")
screen.bgcolor("black")
screen.setup(width=800, height=600)

# Create a paddle on the right side of the screen
right_paddle = turtle.Turtle()
right_paddle.speed(0)
right_paddle.shape("square")
right_paddle.color("white")
right_paddle.shapesize(stretch_wid=5, stretch_len=1)
right_paddle.penup()
right_paddle.goto(-350, 0)

# Create a paddle on the left side of the screen
left_paddle = turtle.Turtle()
left_paddle.speed(0)
left_paddle.shape("square")
left_paddle.color("white")
left_paddle.shapesize(stretch_wid=5, stretch_len=1)
left_paddle.penup()
left_paddle.goto(350, 0)

# Create the ball and move it to the screen center
ball = turtle.Turtle()
ball.speed(40)
ball.shape("circle")
ball.color("white")
ball.penup()
ball.goto(0, 0)
ball.dx = 2.5
ball.dy = -2.5

# Function to move the right paddle up
def right_paddle_up():
    y = right_paddle.ycor()
    if y < 250:
        y += 20
    right_paddle.sety(y)

# Function to move the right paddle down
def right_paddle_down():
    y = right_paddle.ycor()
    if y > -250:
        y -= 20
    right_paddle.sety(y)

# Function to move the left paddle up
def left_paddle_up():
    y = left_paddle.ycor()
    if y < 250:
        y += 20
    left_paddle.sety(y)

# Function to move the left paddle down
def left_paddle_down():
    y = left_paddle.ycor()
    if y > -250:
        y -= 20
    left_paddle.sety(y)

# Keyboard bindings for movement of paddles and ball
screen.listen()
screen.onkeypress(right_paddle_up, "w")
screen.onkeypress(right_paddle_down, "s")
screen.onkeypress(left_paddle_up, "Up")
screen.onkeypress(left_paddle_down, "Down")

while True:
    screen.update()

    # Move the ball
    ball.setx(ball.xcor() + ball.dx)
    ball.sety(ball.ycor() + ball.dy)

    # Define borders for the game
    if ball.ycor() > 290:
        ball.sety(290)
        ball.dy *= -1

    if ball.ycor() < -290:
        ball.sety(-290)
        ball.dy *= -1

    if ball.xcor() > 390:
        ball.goto(0, 0)
        ball.dx *= -1

    if ball.xcor() < -390:
        ball.goto(0, 0)
        ball.dx *= -1