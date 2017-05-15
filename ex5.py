my_name = 'Zed A. Shaw'
my_age = 35 # not a lie
my_height = 74 #inch
my_weight = 180 # lbs
my_eyes = 'Blue'
my_teeth = 'White'
my_hair = 'Brown'

print "Let's talk about %s." % my_name
print "He's %r cm tall." % round(my_height*2.54)
print "he's %r kgs heavy." % round(my_weight/2.20462262)
print "Actually that's not too heavy."
print "He's got %s eyes and %s hair." % (my_eyes, my_hair)
print "His teeth are usually %s depending on the coffee." % my_teeth

# this line is tricky, try to get it exactly right
print "If I add %d, %d, and %d I get %d." % (
   my_age, my_height*2.54, my_weight/2.20462262, my_age + my_height*2.54 + my_weight/2.20462262)
