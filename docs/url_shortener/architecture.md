# Architecture

```mermaid
graph TB
    subgraph presentation [Presentation Layer]
        HTTP[HTTP Protocol]
        Handler[Request Handler]
        Registry[Handler Registry]
    end

    subgraph application [Application Layer]
        Service[Shortener Service]
        BaseService[Base Shortener]
    end

    subgraph domain [Domain Layer]
        Encoder[Base62 Encoder]
        Exceptions[Business Exceptions]
    end

    subgraph infrastructure [Infrastructure Layer]
        Storage[Storage Implementations]
        HTTPUtils[HTTP Utils]
        Config[Configuration]
        Factory[Factory Functions]
    end

    HTTP --> Handler
    Handler --> Registry
    Registry --> Service
    Service --> BaseService
    BaseService --> Storage
    Service --> Encoder
    Service --> Exceptions
    Storage --> Factory
    HTTPUtils --> Factory
    Config --> Factory
    Factory --> Service
```

## Layer Responsibilities

| Layer              | Purpose                             | Key Files                                              |
| ------------------ | ----------------------------------- | ------------------------------------------------------ |
| **Presentation**   | HTTP protocol, request routing      | [`api.py`][api], [`handlers.py`][handlers]             |
| **Application**    | Business logic orchestration        | [`service.py`][service]                                |
| **Domain**         | Core business rules                 | [`encoder.py`][encoder], [`exceptions.py`][exceptions] |
| **Infrastructure** | External concerns (storage, config) | [`storage.py`][storage], [`config.py`][config]         |

[api]: https://github.com/smirnoffmg/pure-python-system-design/blob/main/url_shortener/src/url_shortener/presentation/api.py
[handlers]: https://github.com/smirnoffmg/pure-python-system-design/blob/main/url_shortener/src/url_shortener/presentation/handlers.py
[service]: https://github.com/smirnoffmg/pure-python-system-design/blob/main/url_shortener/src/url_shortener/application/service.py
[encoder]: https://github.com/smirnoffmg/pure-python-system-design/blob/main/url_shortener/src/url_shortener/domain/encoder.py
[exceptions]: https://github.com/smirnoffmg/pure-python-system-design/blob/main/url_shortener/src/url_shortener/domain/exceptions.py
[storage]: https://github.com/smirnoffmg/pure-python-system-design/blob/main/url_shortener/src/url_shortener/infrastructure/storage.py
[config]: https://github.com/smirnoffmg/pure-python-system-design/blob/main/url_shortener/src/url_shortener/infrastructure/config.py
